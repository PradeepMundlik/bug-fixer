package com.bugfixer.backend.repository;

import com.bugfixer.backend.entity.Project;
import com.bugfixer.backend.entity.ProjectStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ProjectRepository extends JpaRepository<Project, UUID> {

    List<Project> findAllByOrderByCreatedAtDesc();

    List<Project> findByStatus(ProjectStatus status);
}
