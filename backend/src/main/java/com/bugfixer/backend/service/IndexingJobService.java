package com.bugfixer.backend.service;

import com.bugfixer.backend.entity.ProjectStatus;
import com.bugfixer.backend.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class IndexingJobService {

    private final ProjectRepository projectRepository;
    private final FileTraversalService fileTraversalService;

    @Async("indexingExecutor")
    public void startIndexing(UUID projectId, String storagePath) {
        log.info("Indexing started for project {}", projectId);

        projectRepository.findById(projectId).ifPresent(project -> {
            try {
                project.setStatus(ProjectStatus.PARSING);
                projectRepository.save(project);

                var files = fileTraversalService.traverseAndPersist(projectId, storagePath);

                project.setFileCount(files.size());
                project.setStatus(ProjectStatus.INDEXED);
                projectRepository.save(project);

                log.info("Indexing complete for project {}: {} files", projectId, files.size());

            } catch (Exception e) {
                log.error("Indexing failed for project {}: {}", projectId, e.getMessage(), e);
                project.setStatus(ProjectStatus.FAILED);
                projectRepository.save(project);
            }
        });
    }
}
