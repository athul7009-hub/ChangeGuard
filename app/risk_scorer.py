
def calculate_risk(
    line_stats: dict,
    all_affected: list,
    related_tests: list,
) -> dict:
    """
    Calculate a preliminary, explainable change-risk score.

    This is a heuristic, not a guarantee of safety.
    Related tests are detected, not executed or verified.
    """
    total_changed_lines = sum(
        stats.get("total_changed_lines", 0)
        for stats in line_stats.values()
    )

    # Count distinct paths, not repeated display entries.
    affected_files = {
        str(path).replace("\\", "/")
        for path in all_affected
    }
    related_test_files = {
        str(path).replace("\\", "/")
        for path in related_tests
    }

    affected_count = len(affected_files)
    test_count = len(related_test_files)

    # Change-size score: 0–40
    size_score = min(total_changed_lines * 2, 40)

    # Dependency-impact score: 0–40
    dependency_score = min(affected_count * 5, 40)

    # Missing-test signal: 20 points
    test_score = 0 if test_count > 0 else 20

    score = min(size_score + dependency_score + test_score, 100)
    if total_changed_lines == 0 and affected_count == 0:
        score = 0
    else:
        score = min(size_score + dependency_score + test_score, 100)

    if score <= 30:
        level = "Low"
    elif score <= 60:
        level = "Medium"
    else:
        level = "High"

    return {
        "score": score,
        "level": level,
        "factors": {
            "changed_lines": total_changed_lines,
            "size_score": size_score,
            "affected_files": affected_count,
            "dependency_score": dependency_score,
            "related_tests_found": test_count,
            "test_signal_score": test_score,
        },
        "note": (
            "Heuristic risk estimate. Related tests are identified "
            "but are not automatically executed or verified. "
            "A lower score does not guarantee a safe change."
        ),
    }
