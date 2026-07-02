package com.bugfixer.backend.repository;

import com.bugfixer.backend.entity.ProjectFile;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ProjectFileRepository extends JpaRepository<ProjectFile, UUID> {

    List<ProjectFile> findByProjectId(UUID projectId);

    long countByProjectId(UUID projectId);
}
