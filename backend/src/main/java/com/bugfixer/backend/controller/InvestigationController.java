package com.bugfixer.backend.controller;

import com.bugfixer.backend.dto.CreateInvestigationRequest;
import com.bugfixer.backend.dto.InvestigationResponse;
import com.bugfixer.backend.service.InvestigationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/investigations")
@RequiredArgsConstructor
public class InvestigationController {

    private final InvestigationService investigationService;

    @PostMapping
    public ResponseEntity<InvestigationResponse> createInvestigation(
            @Valid @RequestBody CreateInvestigationRequest request) {
        InvestigationResponse response = investigationService.createInvestigation(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<InvestigationResponse> getInvestigation(@PathVariable UUID id) {
        return ResponseEntity.ok(investigationService.getInvestigation(id));
    }

    @GetMapping
    public ResponseEntity<List<InvestigationResponse>> listInvestigations(
            @RequestParam UUID projectId) {
        return ResponseEntity.ok(investigationService.listByProject(projectId));
    }
}
