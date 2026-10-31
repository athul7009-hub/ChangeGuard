import os
from pathlib import Path
import subprocess
import sys
import time


DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 12000


def run_related_tests(
    project_root: str,
    related_tests: list[str],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """
    Run validated related pytest files inside the selected project.
    """

    root = Path(project_root).resolve()

    if not root.exists() or not root.is_dir():
        return {
            "status": "error",
            "message": "The selected project folder does not exist.",
            "tests_discovered": 0,
            "tests_executed": [],
            "duration_seconds": 0,
            "exit_code": None,
            "output": "",
        }

    if not related_tests:
        return {
            "status": "not_run",
            "message": "No related tests were discovered.",
            "tests_discovered": 0,
            "tests_executed": [],
            "duration_seconds": 0,
            "exit_code": None,
            "output": "",
        }

    validated_tests = []

    for test_path in related_tests:
        candidate = Path(test_path)

        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (root / candidate).resolve()

            # Also support paths relative to the repository root.
            if not resolved.is_file():
                resolved = (root.parent / candidate).resolve()

        # Do not allow tests outside the selected project.
        if not resolved.is_relative_to(root):
            continue

        if not resolved.is_file():
            continue

        if resolved.suffix != ".py" or not resolved.name.startswith("test_"):
            continue

        if resolved not in validated_tests:
            validated_tests.append(resolved)

    if not validated_tests:
        return {
            "status": "not_run",
            "message": "No valid related test files were found inside the project.",
            "tests_discovered": 0,
            "tests_executed": [],
            "duration_seconds": 0,
            "exit_code": None,
            "output": "",
        }

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        *[str(path) for path in validated_tests],
    ]

        # Prepare Python's import path for nested project packages.
    test_env = os.environ.copy()

    import_paths = [str(root)]
    demo_directory = root / "demo"

    if demo_directory.is_dir():
        import_paths.insert(0, str(demo_directory))

    existing_pythonpath = test_env.get("PYTHONPATH")
    if existing_pythonpath:
        import_paths.append(existing_pythonpath)

    test_env["PYTHONPATH"] = os.pathsep.join(import_paths)
    start_time = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env=test_env,
        )

        duration = round(time.monotonic() - start_time, 2)
        output = (
            (completed.stdout or "") + "\n" + (completed.stderr or "")
        ).strip()

        if completed.returncode == 0:
            status = "passed"
            message = "All selected related tests passed."
        else:
            status = "failed"
            message = "One or more selected tests failed, or pytest encountered an error."

        return {
            "status": status,
            "message": message,
            "tests_discovered": len(validated_tests),
            "tests_executed": [str(path.relative_to(root)) for path in validated_tests],
            "duration_seconds": duration,
            "exit_code": completed.returncode,
            "output": output[-MAX_OUTPUT_CHARS:],
        }

    except subprocess.TimeoutExpired as error:
        duration = round(time.monotonic() - start_time, 2)
        partial_output = error.stdout or ""
        if isinstance(partial_output, bytes):
            partial_output = partial_output.decode("utf-8", errors="replace")

        return {
            "status": "timed_out",
            "message": f"Test execution exceeded the {timeout_seconds}-second timeout.",
            "tests_discovered": len(validated_tests),
            "tests_executed": [str(path.relative_to(root)) for path in validated_tests],
            "duration_seconds": duration,
            "exit_code": None,
            "output": partial_output[-MAX_OUTPUT_CHARS:],
        }

    except OSError as error:
        return {
            "status": "error",
            "message": f"Could not start pytest: {error}",
            "tests_discovered": len(validated_tests),
            "tests_executed": [str(path.relative_to(root)) for path in validated_tests],
            "duration_seconds": round(time.monotonic() - start_time, 2),
            "exit_code": None,
            "output": "",
        }
