from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable, List


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "raw",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".gz", ".zip"}
INCLUDED_TOP_LEVELS = {
    "data",
    "reports",
    "results",
    "scripts",
    "src",
    "tests",
}
INCLUDED_ROOT_FILES = {
    "README.md",
    "requirements.txt",
    "agent.md",
    "MinerU_markdown_北斗定位解算全流程软件系统开发实验题目_2049408313226227712.md",
}


def build_submission_file_list(root: str | Path) -> List[Path]:
    root_path = Path(root)
    files: List[Path] = []
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root_path)
        if _should_include(rel):
            files.append(rel)
    return sorted(files)


def create_submission_zip(root: str | Path, output_zip: str | Path, files: Iterable[Path] | None = None) -> Path:
    root_path = Path(root)
    output_path = Path(output_zip)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected_files = list(files) if files is not None else build_submission_file_list(root_path)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in selected_files:
            archive.write(root_path / rel, arcname=rel.as_posix())
    return output_path


def _should_include(rel: Path) -> bool:
    parts = rel.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return False
    if rel.suffix in EXCLUDED_SUFFIXES:
        return False
    if len(parts) == 1:
        return rel.name in INCLUDED_ROOT_FILES
    return parts[0] in INCLUDED_TOP_LEVELS
