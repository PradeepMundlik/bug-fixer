package com.bugfixer.backend.service;

import com.bugfixer.backend.dto.IndexFileRequest;
import com.bugfixer.backend.dto.IndexFileResponse;
import com.bugfixer.backend.dto.PlanDto;
import com.bugfixer.backend.dto.PlanRequestDto;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

@Service
@Slf4j
public class AiServiceClient {

    private String aiServiceUrl;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public AiServiceClient(
            RestTemplateBuilder builder,
            @Value("${ai.service.url}") String aiServiceUrl) {
        // Force the RestTemplate to use the JDK HttpURLConnection (HTTP/1.1)
        this.restTemplate = new org.springframework.web.client.RestTemplate(new SimpleClientHttpRequestFactory());
        this.aiServiceUrl = aiServiceUrl;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
    }

    public IndexFileResponse indexFile(IndexFileRequest request) {
        String url = aiServiceUrl + "/index";
        log.debug("Calling AI service: POST {} for file {}", url, request.getFilePath());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        try {
            String jsonBody = objectMapper.writeValueAsString(request);
            HttpEntity<String> entity = new HttpEntity<>(jsonBody, headers);
            return restTemplate.postForObject(url, entity, IndexFileResponse.class);

        } catch (Exception e) {
            throw new RuntimeException("Failed to call AI service for file: " + request.getFilePath(), e);
        }
    }

    public PlanDto createPlan(PlanRequestDto request) {
        String url = aiServiceUrl + "/plan";
        log.debug("Calling AI service: POST {} for project {}", url, request.getProjectId());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        try {
            String jsonBody = objectMapper.writeValueAsString(request);
            HttpEntity<String> entity = new HttpEntity<>(jsonBody, headers);
            return restTemplate.postForObject(url, entity, PlanDto.class);

        } catch (HttpStatusCodeException e) {
            // Surface the Python error body (e.g. 422 invalid plan, 502 LLM error)
            throw new RuntimeException(
                    "AI /plan failed (" + e.getStatusCode() + "): " + e.getResponseBodyAsString(), e);
        } catch (Exception e) {
            throw new RuntimeException("Failed to call AI /plan: " + e.getMessage(), e);
        }
    }
}
