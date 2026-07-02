package com.bugfixer.backend.dto;

import com.bugfixer.backend.entity.ProjectStatus;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
public class ProjectResponse {
    private UUID id;
    private String name;
    private ProjectStatus status;
    private Integer fileCount;
    private String originalFilename;
    private String storagePath;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
