import os

# Root directory where the backend extracts uploaded projects.
# Each project lives at {PROJECT_STORAGE_ROOT}/{project_id}/{relative_file_path}.
# Must match BASE_STORAGE in the Spring backend (ProjectService.java) and be
# mounted into the ai-service container via docker-compose so read_file/grep
# can reach the files.
PROJECT_STORAGE_ROOT = os.getenv("PROJECT_STORAGE_ROOT", "/tmp/bug-fixer")
