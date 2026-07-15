package com.bugfixer.backend.exception;

import java.util.UUID;

public class InvestigationNotFoundException extends RuntimeException {

    public InvestigationNotFoundException(UUID id) {
        super("Investigation not found with id: " + id);
    }
}
