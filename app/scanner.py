
from pathlib import Path


def scan_python_files(project_path: str) -> list[Path]:
    """
    Find all Python files inside the given project folder.
    """
    root = Path(project_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Project folder not found: {project_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Expected a folder, received: {project_path}"
        )

    ignored_directories = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
    }

    python_files = []

    for file_path in root.rglob("*.py"):
        if any(
            part in ignored_directories
            for part in file_path.parts
        ):
            continue

        python_files.append(file_path)

    return sorted(python_files)
