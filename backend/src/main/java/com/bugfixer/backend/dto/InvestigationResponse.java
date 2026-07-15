package com.bugfixer.backend.dto;

import com.bugfixer.backend.entity.Investigation;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
public class InvestigationResponse {
    private UUID id;
    private UUID projectId;
    private String bugDescription;
    private String status;
    private PlanDto plan;
    private String summary;
    private String errorMessage;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static InvestigationResponse from(Investigation inv) {
        return InvestigationResponse.builder()
                .id(inv.getId())
                .projectId(inv.getProjectId())
                .bugDescription(inv.getBugDescription())
                .status(inv.getStatus() != null ? inv.getStatus().name() : null)
                .plan(inv.getPlanJson())
                .summary(inv.getSummary())
                .errorMessage(inv.getErrorMessage())
                .createdAt(inv.getCreatedAt())
                .updatedAt(inv.getUpdatedAt())
                .build();
    }
}
