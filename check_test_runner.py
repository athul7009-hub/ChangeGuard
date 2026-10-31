
from pathlib import Path
from app.test_runner import run_related_tests

project_root = Path("sample_project").resolve()
related_tests = ["test_calculator.py"]

result = run_related_tests(
    project_root=str(project_root),
    related_tests=related_tests,
)

print(result)
