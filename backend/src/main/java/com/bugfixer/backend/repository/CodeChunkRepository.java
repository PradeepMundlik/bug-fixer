package com.bugfixer.backend.repository;

import com.bugfixer.backend.entity.CodeChunk;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface CodeChunkRepository extends JpaRepository<CodeChunk, UUID> {

    List<CodeChunk> findByFileId(UUID fileId);

    List<CodeChunk> findByProjectId(UUID projectId);
}
