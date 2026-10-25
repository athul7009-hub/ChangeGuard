
from pathlib import Path

from app.graph_builder import build_dependency_graph


project_path = Path("sample_project")

graph = build_dependency_graph(str(project_path))

print("Files discovered:", graph.number_of_nodes())
print("Dependencies found:", graph.number_of_edges())

print("\nDependency relationships:")

for dependency, dependent in graph.edges():
    print(
        f"{Path(dependency).name} -> "
        f"{Path(dependent).name}"
    )
