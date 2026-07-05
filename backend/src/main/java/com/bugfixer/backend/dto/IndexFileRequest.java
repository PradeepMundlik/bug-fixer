package com.bugfixer.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class IndexFileRequest {
    @JsonProperty("file_content")
    private String fileContent;

    @JsonProperty("file_path")
    private String filePath;

    @JsonProperty("project_id")
    private String projectId;

    @JsonProperty("file_id")
    private String fileId;

    private String language;
}
