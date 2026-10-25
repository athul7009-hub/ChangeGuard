
from pathlib import Path

import networkx as nx


def analyze_impact(
    graph: nx.DiGraph,
    changed_file: str,
) -> dict:
    """
    Find files potentially affected by a change.

    Graph edges point from dependencies to dependent files.
    """
    target = Path(changed_file).resolve()

    # Match the changed file against the graph's absolute paths.
    graph_nodes = set(graph.nodes())

    if str(target) not in graph_nodes:
        matches = [
            node
            for node in graph_nodes
            if Path(node).name == target.name
        ]

        if len(matches) == 1:
            target = Path(matches[0])
        else:
            raise ValueError(
                f"Changed file not found or ambiguous: {changed_file}"
            )

    target_node = str(target)

    # Find every file reachable from the changed file.
    affected_nodes = nx.descendants(graph, target_node)

    # Direct dependents are one edge away.
    direct_nodes = set(graph.successors(target_node))

    # Indirect dependents are affected files beyond the first level.
    indirect_nodes = affected_nodes - direct_nodes

    def display_path(node: str) -> str:
        return Path(node).name

    return {
        "changed_file": display_path(target_node),
        "directly_affected": sorted(
            display_path(node) for node in direct_nodes
        ),
        "indirectly_affected": sorted(
            display_path(node) for node in indirect_nodes
        ),
        "all_affected": sorted(
            display_path(node) for node in affected_nodes
        ),
        "related_tests": sorted(
            display_path(node)
            for node in affected_nodes
            if Path(node).name.startswith("test_")
            or Path(node).name.endswith("_test.py")
        ),
    }
