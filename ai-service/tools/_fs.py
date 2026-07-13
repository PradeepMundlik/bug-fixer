from pathlib import Path
from typing import Optional

from app.config import PROJECT_STORAGE_ROOT


def project_root(project_id: str) -> Path:
    return (Path(PROJECT_STORAGE_ROOT) / project_id).resolve()


def resolve_within_project(project_id: str, rel_path: Optional[str]) -> Path:
    """
    Resolve ``rel_path`` against the project's extracted-files root, refusing any
    path that escapes it (Zip-Slip style ``../`` traversal or absolute paths).
    """
    root = project_root(project_id)
    target = (root / (rel_path or "")).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes project root: {rel_path!r}")
    return target
