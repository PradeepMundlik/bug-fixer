package com.bugfixer.backend.service;

import com.bugfixer.backend.dto.ProjectResponse;
import com.bugfixer.backend.dto.ProjectStatusResponse;
import com.bugfixer.backend.dto.UploadResponse;
import com.bugfixer.backend.entity.Project;
import com.bugfixer.backend.entity.ProjectFile;
import com.bugfixer.backend.entity.ProjectStatus;
import com.bugfixer.backend.exception.ProjectNotFoundException;
import com.bugfixer.backend.repository.ProjectFileRepository;
import com.bugfixer.backend.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

@Service
@RequiredArgsConstructor
@Slf4j
public class ProjectService {

    private static final String BASE_STORAGE = "/tmp/bug-fixer";

    private final ProjectRepository projectRepository;
    private final ProjectFileRepository projectFileRepository;
    private final IndexingJobService indexingJobService;

    @Transactional
    public UploadResponse uploadProject(String projectName, MultipartFile zipFile) {
        Project project = projectRepository.save(
            Project.builder()
                .name(projectName)
                .status(ProjectStatus.UPLOADED)
                .originalFilename(zipFile.getOriginalFilename())
                .build()
        );

        UUID projectId = project.getId();
        Path extractDir = Paths.get(BASE_STORAGE, projectId.toString());

        try {
            Files.createDirectories(extractDir);

            List<ProjectFile> files = new ArrayList<>();
            try (ZipInputStream zis = new ZipInputStream(zipFile.getInputStream())) {
                ZipEntry entry;
                while ((entry = zis.getNextEntry()) != null) {
                    if (entry.isDirectory()) {
                        Files.createDirectories(extractDir.resolve(entry.getName()));
                        zis.closeEntry();
                        continue;
                    }

                    Path targetFile = extractDir.resolve(entry.getName());
                    // Zip Slip protection: reject any path that escapes the extraction directory
                    if (!targetFile.normalize().startsWith(extractDir.normalize())) {
                        throw new IOException("Zip Slip detected: " + entry.getName());
                    }

                    Files.createDirectories(targetFile.getParent());
                    Files.copy(zis, targetFile, StandardCopyOption.REPLACE_EXISTING);

                    long size = entry.getSize() > 0 ? entry.getSize() : targetFile.toFile().length();
                    files.add(ProjectFile.builder()
                        .projectId(projectId)
                        .filePath(entry.getName())
                        .language(detectLanguage(entry.getName()))
                        .sizeBytes(size)
                        .build()
                    );

                    zis.closeEntry();
                }
            }

            projectFileRepository.saveAll(files);

            project.setStoragePath(extractDir.toString());
            project.setFileCount(files.size());
            projectRepository.save(project);

            log.info("Project {} uploaded: {} files extracted to {}", projectId, files.size(), extractDir);

            // Kick off async indexing only after this transaction commits —
            // the background thread needs the project row to be visible in the DB.
            String extractDirStr = extractDir.toString();
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    indexingJobService.startIndexing(projectId, extractDirStr);
                }
            });

            return UploadResponse.builder()
                .projectId(projectId)
                .projectName(project.getName())
                .status(project.getStatus())
                .fileCount(files.size())
                .storagePath(extractDir.toString())
                .build();

        } catch (IOException e) {
            project.setStatus(ProjectStatus.FAILED);
            projectRepository.save(project);
            log.error("Upload failed for project {}: {}", projectId, e.getMessage());
            throw new RuntimeException("Failed to process zip file: " + e.getMessage(), e);
        }
    }

    @Transactional(readOnly = true)
    public List<ProjectResponse> listProjects() {
        return projectRepository.findAllByOrderByCreatedAtDesc()
            .stream()
            .map(this::toProjectResponse)
            .toList();
    }

    @Transactional(readOnly = true)
    public ProjectResponse getProject(UUID id) {
        Project project = projectRepository.findById(id)
            .orElseThrow(() -> new ProjectNotFoundException(id));
        return toProjectResponse(project);
    }

    @Transactional(readOnly = true)
    public ProjectStatusResponse getProjectStatus(UUID id) {
        Project project = projectRepository.findById(id)
            .orElseThrow(() -> new ProjectNotFoundException(id));
        return ProjectStatusResponse.builder()
            .projectId(project.getId())
            .projectName(project.getName())
            .status(project.getStatus())
            .fileCount(project.getFileCount())
            .build();
    }

    private ProjectResponse toProjectResponse(Project project) {
        return ProjectResponse.builder()
            .id(project.getId())
            .name(project.getName())
            .status(project.getStatus())
            .fileCount(project.getFileCount())
            .originalFilename(project.getOriginalFilename())
            .storagePath(project.getStoragePath())
            .createdAt(project.getCreatedAt())
            .updatedAt(project.getUpdatedAt())
            .build();
    }

    private String detectLanguage(String filename) {
        if (filename == null) return "unknown";
        int dot = filename.lastIndexOf('.');
        if (dot < 0) return "unknown";
        return switch (filename.substring(dot + 1).toLowerCase()) {
            case "java"            -> "java";
            case "py"              -> "python";
            case "js"              -> "javascript";
            case "ts"              -> "typescript";
            case "go"              -> "go";
            case "rs"              -> "rust";
            case "cpp", "cc", "cxx" -> "cpp";
            case "c"               -> "c";
            case "rb"              -> "ruby";
            case "cs"              -> "csharp";
            case "kt"              -> "kotlin";
            case "scala"           -> "scala";
            case "php"             -> "php";
            case "swift"           -> "swift";
            case "md"              -> "markdown";
            case "json"            -> "json";
            case "yaml", "yml"     -> "yaml";
            case "xml"             -> "xml";
            case "sql"             -> "sql";
            case "sh", "bash"      -> "shell";
            default                -> "unknown";
        };
    }
}
