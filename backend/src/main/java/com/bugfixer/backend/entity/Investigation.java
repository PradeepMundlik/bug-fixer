package com.bugfixer.backend.entity;

import com.bugfixer.backend.dto.PlanDto;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "investigations")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Investigation {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(updatable = false, nullable = false)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "bug_description", nullable = false, columnDefinition = "TEXT")
    private String bugDescription;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    @Builder.Default
    private InvestigationStatus status = InvestigationStatus.PLANNING;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "plan_json", columnDefinition = "jsonb")
    private PlanDto planJson;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    // Populated in later days (root cause analysis)
    @Column(name = "root_cause", columnDefinition = "TEXT")
    private String rootCause;

    @Column(name = "relevant_context", columnDefinition = "TEXT")
    private String relevantContext;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
