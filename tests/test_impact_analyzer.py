
from pathlib import Path

from app.graph_builder import build_dependency_graph
from app.impact_analyzer import analyze_impact


PROJECT_PATH = Path(__file__).resolve().parents[1] / "sample_project"


def test_calculator_impact():
    graph = build_dependency_graph(str(PROJECT_PATH))

    result = analyze_impact(
        graph,
        str(PROJECT_PATH / "calculator.py"),
    )

    assert result["changed_file"] == "calculator.py"
    assert set(result["directly_affected"]) == {
        "pipeline.py",
        "test_calculator.py",
    }
    assert set(result["indirectly_affected"]) == {"main.py"}
    assert set(result["related_tests"]) == {"test_calculator.py"}


def test_evaluator_impact():
    graph = build_dependency_graph(str(PROJECT_PATH))

    result = analyze_impact(
        graph,
        str(PROJECT_PATH / "evaluator.py"),
    )

    assert set(result["directly_affected"]) == {"pipeline.py"}
    assert set(result["indirectly_affected"]) == {"main.py"}


def test_unknown_file_raises_error():
    graph = build_dependency_graph(str(PROJECT_PATH))

    try:
        analyze_impact(graph, "missing_file.py")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for an unknown file")
