package com.bugfixer.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class ChunkResultDto {
    @JsonProperty("chunk_type")
    private String chunkType;
    @JsonProperty("method_name")
    private String methodName;
    @JsonProperty("class_name")
    private String className;
    private String content;
    @JsonProperty("start_line")
    private int startLine;
    @JsonProperty("end_line")
    private int endLine;
    private List<String> annotations;
    private List<String> callees;
    @JsonProperty("qdrant_point_id")
    private String qdrantPointId;
}
