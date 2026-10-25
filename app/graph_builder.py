
from pathlib import Path

import networkx as nx

from app.parser import parse_imports
from app.scanner import scan_python_files


def build_dependency_graph(project_path: str) -> nx.DiGraph:
    root = Path(project_path).resolve()
    python_files = [
        Path(path).resolve()
        for path in scan_python_files(str(root))
    ]

    graph = nx.DiGraph()
    module_to_file = {}

    # Build module names from paths relative to the project root.
    for file_path in python_files:
        try:
            relative_path = file_path.relative_to(root)
        except ValueError:
            continue

        module_name = ".".join(relative_path.with_suffix("").parts)

        if module_name.endswith(".__init__"):
            module_name = module_name[:-len(".__init__")]

        if module_name:
            module_to_file[module_name] = file_path

    for file_path in python_files:
        graph.add_node(str(file_path))

    def resolve_module(module_name: str):
        # Prefer the exact module path.
        if module_name in module_to_file:
            return module_to_file[module_name]

        # Try matching a module by its final name.
        # Example: shop_demo.pricing -> pricing
        matches = [
            path
            for name, path in module_to_file.items()
            if name == module_name.split(".")[-1]
            or name.endswith("." + module_name)
            or module_name.endswith("." + name)
        ]

        # Avoid connecting to an arbitrary file if ambiguous.
        unique_matches = set(matches)
        if len(unique_matches) == 1:
            return next(iter(unique_matches))

        return None

    for file_path in python_files:
        importing_file = str(file_path)

        for module_name in parse_imports(file_path):
            dependency_file = resolve_module(module_name)

            # Handle common relative imports, e.g. from . import pricing.
            if dependency_file is None and module_name.startswith("."):
                continue

            if dependency_file is not None:
                dependency_path = str(dependency_file)

                if dependency_path != importing_file:
                    graph.add_edge(dependency_path, importing_file)

    return graph
