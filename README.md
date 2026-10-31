# ChangeGuard — AI-Powered Code Change Impact Analyzer

ChangeGuard is a Python-based tool that analyzes code changes, identifies potentially affected files, visualizes dependencies, and uses a locally running AI model to explain the possible impact of changes.

It helps developers understand what might break before they commit or merge code changes.

## Key Features

- **Project Scanning:** Scans Python projects and identifies source files.
- **Dependency Analysis:** Builds a dependency graph using NetworkX.
- **Impact Analysis:** Identifies directly and indirectly affected files.
- **Git Integration:** Analyzes changes between Git revisions.
- **Visual Dependency Graph:** Displays relationships between changed and affected files.
- **AI-Powered Explanations:** Uses Ollama with Qwen3 8B to generate local explanations.
- **Risk Scoring:** Estimates change risk using factors such as changed lines and affected files.
- **Related Test Detection:** Identifies potentially relevant test files.
- **Test Execution:** Runs related tests through pytest with validation and timeout handling.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| FastAPI | Backend API and web interface |
| NetworkX | Dependency graph construction |
| Git | Change and revision analysis |
| Ollama | Local AI model integration |
| Qwen3 8B | AI-generated explanations |
| Pytest | Automated test execution |

## System Workflow

1. Select a Python project.
2. ChangeGuard scans its Python files.
3. The dependency analyzer builds a graph of file relationships.
4. Select a changed file or compare Git revisions.
5. ChangeGuard identifies potentially affected files.
6. The risk scorer estimates the change risk.
7. Related tests are identified and can be executed.
8. Ollama generates an explanation of the potential impact.

## Project Structure

```text
ChangeGuard/
├── app/
│   ├── main.py
│   ├── impact_analyzer.py
│   ├── git_analyzer.py
│   ├── git_impact_analyzer.py
│   ├── risk_scorer.py
│   └── test_runner.py
├── tests/
├── .gitignore
└── README.md
```

## Requirements

- Python 3.11 or compatible version
- Git
- Ollama
- Qwen3 8B model
- Python dependencies listed in the project's dependency file

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/athul7009-hub/ChangeGuard.git
cd ChangeGuard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the dependencies specified by the project's dependency file.

### 4. Set up Ollama

Install Ollama and pull the model:

```bash
ollama pull qwen3:8b
```

Make sure Ollama is running before using the AI explanation feature.

### 5. Run ChangeGuard

Start the FastAPI application using the project's configured Uvicorn entry point.

## Current Project Status

ChangeGuard includes dependency analysis, Git-based impact analysis, local AI explanations, risk scoring, and related test execution.

## Future Improvements

- Support for additional programming languages.
- More advanced dependency analysis.
- Improved risk prediction.
- CI/CD integration.
- Historical change analysis.

## Author

**Athul Krishna C.R.**

GitHub: [@athul7009-hub](https://github.com/athul7009-hub)

---

*ChangeGuard — Understand the impact before you commit.*