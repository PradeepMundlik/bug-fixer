package com.bugfixer.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
public class PlanStepDto {
    private int step;
    private String goal;
    private String tool;

    // Kept snake_case to match the Python planner output; values may contain
    // "<from step N>" placeholders resolved later by an executor.
    @JsonProperty("tool_input")
    private Map<String, Object> toolInput;

    private String reasoning;
}
