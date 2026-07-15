package com.bugfixer.backend.service;

import com.bugfixer.backend.dto.PlanDto;
import com.bugfixer.backend.dto.PlanRequestDto;
import com.bugfixer.backend.entity.InvestigationStatus;
import com.bugfixer.backend.repository.InvestigationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class InvestigationJobService {

    private final InvestigationRepository investigationRepository;
    private final AiServiceClient aiServiceClient;

    /**
     * Call the Python /plan endpoint and persist the result. Runs on a background
     * thread after the investigation row has committed. Any failure is captured on
     * the record as status FAILED + errorMessage rather than propagated.
     */
    @Async("planningExecutor")
    public void runPlanning(UUID id, UUID projectId, String bugDescription) {
        log.info("Planning started for investigation {}", id);

        investigationRepository.findById(id).ifPresent(inv -> {
            try {
                PlanDto plan = aiServiceClient.createPlan(
                        new PlanRequestDto(bugDescription, projectId.toString()));

                inv.setPlanJson(plan);
                inv.setSummary(plan.getSummary());
                inv.setStatus(InvestigationStatus.PLANNED);

                int steps = plan.getSteps() != null ? plan.getSteps().size() : 0;
                log.info("Investigation {}: plan ready with {} steps", id, steps);

            } catch (Exception e) {
                inv.setStatus(InvestigationStatus.FAILED);
                inv.setErrorMessage(e.getMessage());
                log.error("Planning failed for investigation {}: {}", id, e.getMessage(), e);
            }

            investigationRepository.save(inv);
        });
    }
}
