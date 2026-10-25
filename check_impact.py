
from pathlib import Path

from app.graph_builder import build_dependency_graph
from app.impact_analyzer import analyze_impact


project_path = Path("sample_project")

graph = build_dependency_graph(str(project_path))

result = analyze_impact(
    graph,
    str(project_path / "calculator.py"),
)

print("CHANGEGUARD IMPACT REPORT")
print("=" * 30)

for section, files in result.items():
    print(f"{section}: {files}")
