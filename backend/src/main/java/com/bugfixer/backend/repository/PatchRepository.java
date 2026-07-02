package com.bugfixer.backend.repository;

import com.bugfixer.backend.entity.Patch;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface PatchRepository extends JpaRepository<Patch, UUID> {

    List<Patch> findByInvestigationId(UUID investigationId);

    List<Patch> findByProjectId(UUID projectId);
}
