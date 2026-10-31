
# from pathlib import Path

# import networkx as nx


# def analyze_impact(
#     graph: nx.DiGraph,
#     changed_file: str,
# ) -> dict:
#     """
#     Find files potentially affected by a change.

#     Graph edges point from dependencies to dependent files.
#     """
#     target = Path(changed_file).resolve()

#     # Match the changed file against the graph's absolute paths.
#     graph_nodes = set(graph.nodes())

#     if str(target) not in graph_nodes:
#         matches = [
#             node
#             for node in graph_nodes
#             if Path(node).name == target.name
#         ]

#         if len(matches) == 1:
#             target = Path(matches[0])
#         else:
#             raise ValueError(
#                 f"Changed file not found or ambiguous: {changed_file}"
#             )

#     target_node = str(target)

#     # Find every file reachable from the changed file.
#     affected_nodes = nx.descendants(graph, target_node)

#     # Direct dependents are one edge away.
#     direct_nodes = set(graph.successors(target_node))

#     # Indirect dependents are affected files beyond the first level.
#     indirect_nodes = affected_nodes - direct_nodes

#     def display_path(node: str) -> str:
#         return Path(node).name

#     return {
#         "changed_file": display_path(target_node),
#         "directly_affected": sorted(
#             display_path(node) for node in direct_nodes
#         ),
#         "indirectly_affected": sorted(
#             display_path(node) for node in indirect_nodes
#         ),
#         "all_affected": sorted(
#             display_path(node) for node in affected_nodes
#         ),
#         "related_tests": sorted(
#             display_path(node)
#             for node in affected_nodes
#             if Path(node).name.startswith("test_")
#             or Path(node).name.endswith("_test.py")
#         ),
#     }

from pathlib import Path

import networkx as nx


def analyze_impact(
    graph: nx.DiGraph,
    changed_file: str,
    project_root: str | None = None,
) -> dict:
    """
    Find files potentially affected by a change.

    Graph edges point from dependencies to dependent files.
    """
    target = Path(changed_file).resolve()
    graph_nodes = {str(Path(node).resolve()) for node in graph.nodes()}

    # Match the changed file to a graph node.
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

    affected_nodes = nx.descendants(graph, target_node)
    direct_nodes = set(graph.successors(target_node))
    indirect_nodes = affected_nodes - direct_nodes

    # Prefer project-relative paths so same-named files remain distinct.
    root = (
        Path(project_root).expanduser().resolve()
        if project_root
        else None
    )

    def display_path(node: str) -> str:
        path = Path(node).resolve()

        if root is not None:
            try:
                return path.relative_to(root).as_posix()
            except ValueError:
                pass

        return path.name

    def display_nodes(nodes: set) -> list:
        return sorted({display_path(node) for node in nodes})

    related_test_nodes = {
        node
        for node in affected_nodes
        if Path(node).name.startswith("test_")
        or Path(node).name.endswith("_test.py")
    }

    return {
        "changed_file": display_path(target_node),
        "directly_affected": display_nodes(direct_nodes),
        "indirectly_affected": display_nodes(indirect_nodes),
        "all_affected": display_nodes(affected_nodes),
        "related_tests": display_nodes(related_test_nodes),
    }
