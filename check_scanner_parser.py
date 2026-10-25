
from pathlib import Path

from app.scanner import scan_python_files
from app.parser import parse_imports


project_path = Path("sample_project")

files = scan_python_files(str(project_path))

print("Python files discovered:")
for file_path in files:
    print(" -", file_path)

print("\nImports found:")
for file_path in files:
    imports = parse_imports(file_path)
    print(f"{file_path.name}: {sorted(imports)}")
