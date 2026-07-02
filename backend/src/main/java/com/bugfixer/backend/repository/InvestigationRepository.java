package com.bugfixer.backend.repository;

import com.bugfixer.backend.entity.Investigation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface InvestigationRepository extends JpaRepository<Investigation, UUID> {

    List<Investigation> findByProjectIdOrderByCreatedAtDesc(UUID projectId);
}
