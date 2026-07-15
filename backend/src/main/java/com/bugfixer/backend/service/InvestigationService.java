package com.bugfixer.backend.service;

import com.bugfixer.backend.dto.CreateInvestigationRequest;
import com.bugfixer.backend.dto.InvestigationResponse;
import com.bugfixer.backend.entity.Investigation;
import com.bugfixer.backend.entity.InvestigationStatus;
import com.bugfixer.backend.exception.InvestigationNotFoundException;
import com.bugfixer.backend.exception.ProjectNotFoundException;
import com.bugfixer.backend.repository.InvestigationRepository;
import com.bugfixer.backend.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class InvestigationService {

    private final InvestigationRepository investigationRepository;
    private final ProjectRepository projectRepository;
    private final InvestigationJobService investigationJobService;

    @Transactional
    public InvestigationResponse createInvestigation(CreateInvestigationRequest request) {
        UUID projectId = request.getProjectId();
        if (!projectRepository.existsById(projectId)) {
            throw new ProjectNotFoundException(projectId);
        }

        Investigation investigation = investigationRepository.save(
            Investigation.builder()
                .projectId(projectId)
                .bugDescription(request.getBugDescription())
                .status(InvestigationStatus.PLANNING)
                .build()
        );

        UUID investigationId = investigation.getId();
        String bugDescription = request.getBugDescription();

        // Kick off async planning only after this transaction commits — the background
        // thread needs the investigation row to be visible in the DB.
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                investigationJobService.runPlanning(investigationId, projectId, bugDescription);
            }
        });

        log.info("Investigation {} created for project {} (status PLANNING)", investigationId, projectId);
        return InvestigationResponse.from(investigation);
    }

    @Transactional(readOnly = true)
    public InvestigationResponse getInvestigation(UUID id) {
        Investigation investigation = investigationRepository.findById(id)
            .orElseThrow(() -> new InvestigationNotFoundException(id));
        return InvestigationResponse.from(investigation);
    }

    @Transactional(readOnly = true)
    public List<InvestigationResponse> listByProject(UUID projectId) {
        return investigationRepository.findByProjectIdOrderByCreatedAtDesc(projectId)
            .stream()
            .map(InvestigationResponse::from)
            .toList();
    }
}
