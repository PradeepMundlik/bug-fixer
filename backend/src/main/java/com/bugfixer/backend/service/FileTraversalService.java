package com.bugfixer.backend.service;

import com.bugfixer.backend.entity.ProjectFile;
import com.bugfixer.backend.repository.ProjectFileRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class FileTraversalService {

    private static final Set<String> EXCLUDED_DIRS = Set.of(
        "node_modules", "target", "build", ".git", ".idea", ".gradle",
        "__pycache__", ".pytest_cache", "dist", "out", ".mvn", "venv", ".venv"
    );

    private static final Set<String> INCLUDED_EXTENSIONS = Set.of(
        "java", "py", "js", "ts", "xml", "yaml", "yml",
        "go", "rs", "kt", "scala", "cs", "rb", "php",
        "swift", "c", "cpp", "cc", "cxx", "sql", "sh", "bash", "json", "md"
    );

    private final ProjectFileRepository projectFileRepository;

    @Transactional
    public List<ProjectFile> traverseAndPersist(UUID projectId, String storagePath) throws IOException {
        Path root = Paths.get(storagePath);

        List<ProjectFile> files = new ArrayList<>();

        try (var stream = Files.walk(root)) {
            stream
                .filter(Files::isRegularFile)
                .filter(path -> !isExcluded(root, path))
                .filter(path -> isIncluded(path))
                .forEach(path -> {
                    try {
                        String relativePath = root.relativize(path).toString();
                        String extension = getExtension(path.getFileName().toString());
                        long size = Files.size(path);
                        String hash = computeSha256(path);

                        ProjectFile file = ProjectFile.builder()
                            .projectId(projectId)
                            .filePath(relativePath)
                            .language(detectLanguage(extension))
                            .sizeBytes(size)
                            .contentHash(hash)
                            .build();

                        files.add(file);
                    } catch (IOException e) {
                        log.warn("Skipping file {}: {}", path, e.getMessage());
                    }
                });
        }

        projectFileRepository.saveAll(files);
        log.info("Project {}: {} files traversed and persisted", projectId, files.size());
        return files;
    }

    private boolean isExcluded(Path root, Path path) {
        Path relative = root.relativize(path);
        for (Path part : relative) {
            if (EXCLUDED_DIRS.contains(part.toString())) {
                return true;
            }
        }
        return false;
    }

    private boolean isIncluded(Path path) {
        String ext = getExtension(path.getFileName().toString());
        return INCLUDED_EXTENSIONS.contains(ext);
    }

    private String getExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        if (dot < 0) return "";
        return filename.substring(dot + 1).toLowerCase();
    }

    private String computeSha256(Path path) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = Files.readAllBytes(path);
            return HexFormat.of().formatHex(digest.digest(bytes));
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }

    private String detectLanguage(String ext) {
        return switch (ext) {
            case "java"            -> "java";
            case "py"              -> "python";
            case "js"              -> "javascript";
            case "ts"              -> "typescript";
            case "go"              -> "go";
            case "rs"              -> "rust";
            case "cpp", "cc", "cxx" -> "cpp";
            case "c"               -> "c";
            case "rb"              -> "ruby";
            case "cs"              -> "csharp";
            case "kt"              -> "kotlin";
            case "scala"           -> "scala";
            case "php"             -> "php";
            case "swift"           -> "swift";
            case "md"              -> "markdown";
            case "json"            -> "json";
            case "yaml", "yml"     -> "yaml";
            case "xml"             -> "xml";
            case "sql"             -> "sql";
            case "sh", "bash"      -> "shell";
            default                -> "unknown";
        };
    }
}
