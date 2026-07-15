package com.bugfixer.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request body for the Python /plan endpoint. Serialized with a SNAKE_CASE mapper
 * in AiServiceClient → {"bug_description": ..., "project_id": ...}.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PlanRequestDto {
    private String bugDescription;
    private String projectId;
}
