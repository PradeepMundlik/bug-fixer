package com.bugfixer.backend.controller;

import com.bugfixer.backend.dto.ProjectResponse;
import com.bugfixer.backend.dto.ProjectStatusResponse;
import com.bugfixer.backend.dto.UploadResponse;
import com.bugfixer.backend.service.ProjectService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects")
@RequiredArgsConstructor
public class ProjectController {

    private final ProjectService projectService;

    /**
     * POST /api/projects/upload
     *
     * Postman: Body → form-data
     *   name  (text)  → "my-project"
     *   file  (file)  → select .zip
     */
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<UploadResponse> uploadProject(
            @RequestParam("name") String name,
            @RequestParam("file") MultipartFile file) {

        UploadResponse response = projectService.uploadProject(name, file);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    public ResponseEntity<List<ProjectResponse>> listProjects() {
        return ResponseEntity.ok(projectService.listProjects());
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProjectResponse> getProject(@PathVariable UUID id) {
        return ResponseEntity.ok(projectService.getProject(id));
    }

    @GetMapping("/{id}/status")
    public ResponseEntity<ProjectStatusResponse> getProjectStatus(@PathVariable UUID id) {
        return ResponseEntity.ok(projectService.getProjectStatus(id));
    }
}
