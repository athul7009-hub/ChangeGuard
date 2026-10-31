
from pathlib import Path
from app.risk_scorer import calculate_risk
from app.graph_builder import build_dependency_graph
from app.git_analyzer import get_changed_files
from app.git_analyzer import get_working_tree_changes
from app.impact_analyzer import analyze_impact


def analyze_git_impact(
    project_path: str,
    base_ref: str,
    compare_ref: str,
) -> dict:
    """
    Compare two Git references and analyze the impact
    of changed Python files.
    """
    root = Path(project_path).resolve()

    changes = get_changed_files(
        str(root),
        base_ref,
        compare_ref,
    )

    graph = build_dependency_graph(str(root))

    file_impacts = []
    skipped_files = []

    # Analyze added and modified files that exist in the
    # current project snapshot.
    candidates = changes["added"] + changes["modified"]

    
    for relative_path in candidates:
        candidate = Path(relative_path)

        if candidate.is_absolute():
            full_path = candidate.resolve()
        elif (root / candidate).is_file():
            full_path = (root / candidate).resolve()
        else:
            full_path = (root.parent / candidate).resolve()

        # Ensure the file stays inside the selected project.
        if not full_path.is_relative_to(root):
            skipped_files.append(relative_path)
            continue

        if not full_path.is_file():
            skipped_files.append(relative_path)
            continue

        try:
            impact = analyze_impact(graph, str(full_path))
            file_impacts.append(impact)
        except ValueError:
            skipped_files.append(relative_path)


    # Combine impacted files and tests across all changed files.
    all_affected = set()
    all_tests = set()

    for impact in file_impacts:
        all_affected.update(impact["all_affected"])
        all_tests.update(impact["related_tests"])
    
    risk = calculate_risk(
        line_stats=changes.get("line_stats", {}),
        all_affected=sorted(all_affected),
        related_tests=sorted(all_tests),
    )
    
    return {
        "base_ref": changes["base_ref"],
        "compare_ref": changes["compare_ref"],
        "added": changes["added"],
        "modified": changes["modified"],
        "deleted": changes["deleted"],
        "total_changed": changes["total_changed"],
        "risk": risk,

        # NEW: preserve Git line statistics
        "line_stats": changes.get("line_stats", {}),

        "file_impacts": file_impacts,
        "all_affected": sorted(all_affected),
        "related_tests": sorted(all_tests),
        "skipped_files": skipped_files,
        "note": (
            "Impact is calculated from the current project's "
            "dependency graph. Deleted files are reported separately."
        ),
    }


def analyze_working_tree_impact(project_path: str) -> dict:
    """Analyze local Python changes that have not necessarily been committed."""
    root = Path(project_path).resolve()

    changes = get_working_tree_changes(str(root))
    graph = build_dependency_graph(str(root))

    file_impacts = []
    skipped_files = []

    candidates = changes["added"] + changes["modified"]

    for relative_path in candidates:
        candidate = Path(relative_path)
        full_path = (root / candidate).resolve()

        # Do not analyze paths outside the selected project.
        if not full_path.is_relative_to(root):
            skipped_files.append(relative_path)
            continue

        if not full_path.is_file():
            skipped_files.append(relative_path)
            continue

        try:
            impact = analyze_impact(graph, str(full_path))
            file_impacts.append(impact)
        except ValueError:
            skipped_files.append(relative_path)

    all_affected = set()
    all_tests = set()

    for impact in file_impacts:
        all_affected.update(impact["all_affected"])
        all_tests.update(impact["related_tests"])

    risk = calculate_risk(
        line_stats=changes.get("line_stats", {}),
        all_affected=sorted(all_affected),
        related_tests=sorted(all_tests),
    )

    return {
        "base_ref": changes["base_ref"],
        "compare_ref": changes["compare_ref"],
        "added": changes["added"],
        "modified": changes["modified"],
        "deleted": changes["deleted"],
        "total_changed": changes["total_changed"],
        "risk": risk,
        "line_stats": changes.get("line_stats", {}),
        "file_impacts": file_impacts,
        "all_affected": sorted(all_affected),
        "related_tests": sorted(all_tests),
        "skipped_files": skipped_files,
        "note": (
            "Impact is calculated using the current dependency graph. "
            "Deleted files are listed separately."
        ),
    }
