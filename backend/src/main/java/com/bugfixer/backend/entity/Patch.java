package com.bugfixer.backend.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UuidGenerator;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "patches")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Patch {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(updatable = false, nullable = false)
    private UUID id;

    @Column(name = "investigation_id", nullable = false)
    private UUID investigationId;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "file_path", nullable = false, columnDefinition = "TEXT")
    private String filePath;

    @Column(name = "diff_content", nullable = false, columnDefinition = "TEXT")
    private String diffContent;

    @Column(name = "explanation", columnDefinition = "TEXT")
    private String explanation;

    @Column(name = "status", nullable = false)
    @Builder.Default
    private String status = "DRAFT";

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}
