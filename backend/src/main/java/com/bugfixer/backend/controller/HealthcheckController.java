package com.bugfixer.backend.controller;


import com.bugfixer.backend.dto.ProjectResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/healthcheck")
@RequiredArgsConstructor
public class HealthcheckController {

    @GetMapping
    public ResponseEntity<String> healthcheck() {
        return new ResponseEntity<String>("Bug fixer backend running!", HttpStatus.OK);
    }
}
