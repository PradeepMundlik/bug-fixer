package com.bugfixer.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.UUID;

@Data
public class CreateInvestigationRequest {

    @NotNull(message = "projectId is required")
    private UUID projectId;

    @NotBlank(message = "bugDescription is required")
    private String bugDescription;
}
