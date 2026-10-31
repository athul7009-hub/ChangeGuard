
import subprocess
from pathlib import Path


def run_git_command(project_path: str, *args: str) -> str:
    """Run a Git command inside the selected project folder."""
    folder = Path(project_path).resolve()

    if not folder.is_dir():
        raise ValueError(f"Project folder does not exist: {folder}")

    result = subprocess.run(
        ["git", "-C", str(folder), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise ValueError(message or "Git command failed.")

    return result.stdout.strip()


def get_git_status(project_path: str) -> dict:
    """Check whether a folder is a Git repository."""
    try:
        branch = run_git_command(
            project_path, "branch", "--show-current"
        )
        commit = run_git_command(
            project_path, "rev-parse", "--short", "HEAD"
        )
        return {
            "is_git_repository": True,
            "branch": branch or "(detached HEAD)",
            "commit": commit,
        }
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return {
            "is_git_repository": False,
            "branch": None,
            "commit": None,
        }


def get_changed_files(
    project_path: str,
    base_ref: str,
    compare_ref: str,
) -> dict:
    """
    Compare two Git references and return changed Python files
    with added/deleted line statistics.
    """
    base_ref = base_ref.strip()
    compare_ref = compare_ref.strip()

    if not base_ref or not compare_ref:
        raise ValueError("Both Git references are required.")

    if base_ref.startswith("-") or compare_ref.startswith("-"):
        raise ValueError("Git references cannot start with a hyphen.")

    # Verify that both Git references exist.
    run_git_command(project_path, "rev-parse", "--verify", base_ref)
    run_git_command(project_path, "rev-parse", "--verify", compare_ref)

    # Identify added, modified, and deleted Python files.
    output = run_git_command(
        project_path,
        "diff",
        "--name-status",
        "--no-renames",
        base_ref,
        compare_ref,
        "--",
    )

    changes = {
        "added": [],
        "modified": [],
        "deleted": [],
    }

    for line in output.splitlines():
        parts = line.split("\t", 1)

        if len(parts) != 2:
            continue

        status, filename = parts

        if Path(filename).suffix.lower() != ".py":
            continue

        if status == "A":
            changes["added"].append(filename)
        elif status == "M":
            changes["modified"].append(filename)
        elif status == "D":
            changes["deleted"].append(filename)

    # Count added and deleted lines for each changed Python file.
    numstat_output = run_git_command(
        project_path,
        "diff",
        "--numstat",
        "--no-renames",
        base_ref,
        compare_ref,
        "--",
    )

    line_stats = {}

    for line in numstat_output.splitlines():
        parts = line.split("\t", 2)

        if len(parts) != 3:
            continue

        added_text, deleted_text, filename = parts

        if Path(filename).suffix.lower() != ".py":
            continue

        # Git reports '-' for binary files.
        try:
            added_lines = int(added_text)
            deleted_lines = int(deleted_text)
        except ValueError:
            added_lines = 0
            deleted_lines = 0

        line_stats[filename] = {
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "total_changed_lines": added_lines + deleted_lines,
        }

    return {
        "base_ref": base_ref,
        "compare_ref": compare_ref,
        "added": changes["added"],
        "modified": changes["modified"],
        "deleted": changes["deleted"],
        "total_changed": sum(
            len(files) for files in changes.values()
        ),
        "line_stats": line_stats,
    }

def get_working_tree_changes(project_path: str) -> dict:
    """
    Discover local Python changes, including staged, unstaged,
    and untracked files, relative to HEAD.
    """
    root = Path(project_path).resolve()

    # Confirm that this is a Git repository with a HEAD commit.
    run_git_command(str(root), "rev-parse", "--verify", "HEAD")

    status_output = subprocess.run(
        [
            "git", "-C", str(root),
            "status", "--short", "--untracked-files=all",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )

    if status_output.returncode != 0:
        raise ValueError(
            status_output.stderr.strip() or "Could not read Git status."
        )

    changes = {"added": [], "modified": [], "deleted": []}
    seen = set()

    for line in status_output.stdout.splitlines():
        if len(line) < 4:
            continue

        state = line[:2]
        filename = line[3:]

        # For renames, analyze the destination path.
        if " -> " in filename:
            filename = filename.rsplit(" -> ", 1)[1]

        path = Path(filename)

        if path.suffix.lower() != ".py":
            continue

        if path.is_absolute() or ".." in path.parts:
            continue

        filename = path.as_posix()

        if filename in seen:
            continue
        seen.add(filename)

        if "D" in state:
            changes["deleted"].append(filename)
        elif "?" in state or "A" in state:
            changes["added"].append(filename)
        else:
            changes["modified"].append(filename)

    # Get staged and unstaged line statistics for tracked files.
    numstat_output = run_git_command(
        str(root), "diff", "HEAD", "--numstat", "--no-renames", "--"
    )

    line_stats = {}

    for line in numstat_output.splitlines():
        parts = line.split("\t", 2)

        if len(parts) != 3:
            continue

        added_text, deleted_text, filename = parts

        if Path(filename).suffix.lower() != ".py":
            continue

        try:
            added_lines = int(added_text)
            deleted_lines = int(deleted_text)
        except ValueError:
            added_lines = deleted_lines = 0

        line_stats[filename] = {
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "total_changed_lines": added_lines + deleted_lines,
        }

    # Untracked files are not included in Git diffs, so count their lines.
    for filename in changes["added"]:
        if filename in line_stats:
            continue

        file_path = (root / filename).resolve()

        if file_path.is_relative_to(root) and file_path.is_file():
            try:
                added_lines = len(
                    file_path.read_text(encoding="utf-8").splitlines()
                )
            except (OSError, UnicodeError):
                added_lines = 0

            line_stats[filename] = {
                "added_lines": added_lines,
                "deleted_lines": 0,
                "total_changed_lines": added_lines,
            }

    for category in changes.values():
        category.sort()

    return {
        "base_ref": "HEAD",
        "compare_ref": "WORKING TREE",
        **changes,
        "total_changed": sum(len(files) for files in changes.values()),
        "line_stats": line_stats,
    }
