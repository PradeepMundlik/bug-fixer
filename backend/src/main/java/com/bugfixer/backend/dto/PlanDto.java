package com.bugfixer.backend.dto;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * The investigation plan returned by the Python /plan endpoint, stored as jsonb
 * on the Investigation entity and returned unchanged in the API response.
 */
@Data
@NoArgsConstructor
public class PlanDto {
    private String summary;
    private List<PlanStepDto> steps;
}
