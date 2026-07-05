package com.bugfixer.backend.service;

import com.bugfixer.backend.dto.ChunkResultDto;
import com.bugfixer.backend.dto.IndexFileRequest;
import com.bugfixer.backend.dto.IndexFileResponse;
import com.bugfixer.backend.entity.CodeChunk;
import com.bugfixer.backend.entity.ProjectFile;
import com.bugfixer.backend.entity.ProjectStatus;
import com.bugfixer.backend.repository.CodeChunkRepository;
import com.bugfixer.backend.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class IndexingJobService {

    private final ProjectRepository projectRepository;
    private final CodeChunkRepository codeChunkRepository;
    private final FileTraversalService fileTraversalService;
    private final AiServiceClient aiServiceClient;

    @Async("indexingExecutor")
    public void startIndexing(UUID projectId, String storagePath) {
        log.info("Indexing started for project {}", projectId);

        projectRepository.findById(projectId).ifPresent(project -> {
            try {
                // Phase 1: traverse filesystem, hash files, save to Postgres
                project.setStatus(ProjectStatus.PARSING);
                projectRepository.save(project);

                List<ProjectFile> files = fileTraversalService.traverseAndPersist(projectId, storagePath);
                project.setFileCount(files.size());
                projectRepository.save(project);

                log.info("Project {}: {} files parsed", projectId, files.size());

                // Phase 2: embed each Java file and upsert to Qdrant
                project.setStatus(ProjectStatus.EMBEDDING);
                projectRepository.save(project);

                List<ProjectFile> javaFiles = files.stream()
                    .filter(f -> "java".equals(f.getLanguage()))
                    .toList();

                int totalChunks = embedFiles(projectId, storagePath, javaFiles);

                project.setStatus(ProjectStatus.INDEXED);
                projectRepository.save(project);

                log.info("Project {}: indexed {} chunks from {} Java files",
                    projectId, totalChunks, javaFiles.size());

            } catch (Exception e) {
                log.error("Indexing failed for project {}: {}", projectId, e.getMessage(), e);
                project.setStatus(ProjectStatus.FAILED);
                projectRepository.save(project);
            }
        });
    }

    private int embedFiles(UUID projectId, String storagePath, List<ProjectFile> javaFiles) {
        int totalChunks = 0;

        for (ProjectFile file : javaFiles) {
            try {
                String absolutePath = Paths.get(storagePath, file.getFilePath()).toString();
                String content = readFile(absolutePath);
                if (content.isBlank()) continue;

                IndexFileRequest request = IndexFileRequest.builder()
                    .fileContent(content)
                    .filePath(file.getFilePath())
                    .projectId(projectId.toString())
                    .fileId(file.getId().toString())
                    .language("java")
                    .build();

                IndexFileResponse response = aiServiceClient.indexFile(request);
                if (response == null || response.getChunks() == null) continue;

                saveChunks(projectId, file, response.getChunks());
                totalChunks += response.getChunks().size();

                log.debug("File {}: {} chunks indexed", file.getFilePath(), response.getChunks().size());

            } catch (Exception e) {
                log.warn("Skipping file {} due to error: {}", file.getFilePath(), e.getMessage());
            }
        }

        return totalChunks;
    }

    private void saveChunks(UUID projectId, ProjectFile file, List<ChunkResultDto> chunks) {
        List<CodeChunk> entities = new ArrayList<>();
        for (int i = 0; i < chunks.size(); i++) {
            ChunkResultDto dto = chunks.get(i);
            entities.add(CodeChunk.builder()
                .projectId(projectId)
                .fileId(file.getId())
                .chunkType(dto.getChunkType())
                .chunkIndex(i)
                .startLine(dto.getStartLine())
                .endLine(dto.getEndLine())
                .content(dto.getContent())
                .qdrantPointId(dto.getQdrantPointId())
                .build());
        }
        codeChunkRepository.saveAll(entities);
    }

    private String readFile(String filePath) throws IOException {
        return Files.readString(Paths.get(filePath));
    }
}
