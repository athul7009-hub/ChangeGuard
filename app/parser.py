
import ast
from pathlib import Path


def parse_imports(file_path: Path) -> set[str]:
    """Extract full imported module names from a Python file."""
    try:
        source_code = file_path.read_text(encoding="utf-8")
        syntax_tree = ast.parse(source_code, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    imported_modules = set()

    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

                # Also detect submodules, such as:
                # from package import pricing
                for alias in node.names:
                    if alias.name != "*":
                        imported_modules.add(
                            f"{node.module}.{alias.name}"
                        )

    return imported_modules
