package com.bugfixer.backend.dto;

import com.bugfixer.backend.entity.ProjectStatus;
import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class ProjectStatusResponse {
    private UUID projectId;
    private String projectName;
    private ProjectStatus status;
    private Integer fileCount;
}
