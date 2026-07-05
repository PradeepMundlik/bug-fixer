package com.bugfixer.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class IndexFileResponse {
    @JsonProperty("file_path")
    private String filePath;
    @JsonProperty("project_id")
    private String projectId;
    @JsonProperty("file_id")
    private String fileId;
    private List<ChunkResultDto> chunks;
}
