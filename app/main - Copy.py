from pathlib import Path
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.graph_builder import build_dependency_graph
from app.impact_analyzer import analyze_impact
from app.scanner import scan_python_files

app = FastAPI(
    title="ChangeGuard API",
    description="Analyze the potential impact of Python code changes.",
    version="2.0.0",
)

DEFAULT_PROJECT_PATH = (Path(__file__).resolve().parent.parent / "sample_project").resolve()
PROJECT_PATH = DEFAULT_PROJECT_PATH
MODEL_NAME = "qwen3:8b"


class ProjectRequest(BaseModel):
    project_path: str


class ImpactRequest(BaseModel):
    changed_file: str


HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChangeGuard | Code Impact Analyzer</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 32px 18px; font-family: Arial, sans-serif;
            background: #0f172a; color: #e2e8f0;
        }
        .container { max-width: 900px; margin: auto; }
        h1 { color: #5eead4; margin-bottom: 8px; }
        .subtitle { color: #94a3b8; line-height: 1.5; }
        .panel {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 14px; padding: 22px; margin: 18px 0;
        }
        label { display: block; margin: 14px 0 8px; font-weight: bold; }
        input, select, button {
            width: 100%; padding: 12px; border-radius: 8px; font-size: 15px;
        }
        input, select {
            background: #0f172a; color: #e2e8f0;
            border: 1px solid #475569; margin-bottom: 10px;
        }
        button {
            background: #14b8a6; color: #042f2e; border: 0;
            font-weight: bold; cursor: pointer; margin-top: 8px;
        }
        button:hover { background: #5eead4; }
        button:disabled { opacity: .6; cursor: wait; }
        .secondary { background: #334155; color: #e2e8f0; }
        .secondary:hover { background: #475569; }
        .status { color: #cbd5e1; white-space: pre-wrap; line-height: 1.5; }
        .results { display: none; }
        .result-section { border-top: 1px solid #334155; padding-top: 12px; margin-top: 12px; }
        h2 { font-size: 19px; }
        h3 { font-size: 15px; color: #5eead4; }
        ul { padding-left: 22px; }
        li { margin: 8px 0; overflow-wrap: anywhere; }
        .empty { color: #94a3b8; }
        .ai-box { white-space: pre-wrap; line-height: 1.7; overflow-wrap: anywhere; }
        .path-note { font-size: 13px; color: #94a3b8; }
        .footer { text-align: center; color: #64748b; font-size: 13px; margin-top: 24px; }
    </style>
</head>
<body>
<main class="container">
    <h1>🛡️ ChangeGuard</h1>
    <p class="subtitle">Analyze a Python project and understand which files may be affected by a code change.</p>

    <section class="panel">
        <h2>1. Choose your project folder</h2>
        <p class="path-note">Enter the full folder path on the computer running ChangeGuard. Example: C:\Users\YourName\Desktop\my_project</p>
        <label for="projectPath">Project folder path</label>
        <input id="projectPath" type="text" spellcheck="false" placeholder="C:\path\to\your\python_project">
        <button id="loadButton" onclick="loadProject()">Load project folder</button>
        <p id="projectStatus" class="status">Loading the sample project...</p>
    </section>

    <section class="panel">
        <h2>2. Analyze a code change</h2>
        <label for="changedFile">Select a Python file</label>
        <select id="changedFile" disabled>
            <option value="">Load a project first</option>
        </select>
        <button id="analyzeButton" onclick="analyzeImpact()" disabled>Analyze impact</button>
        <p id="status" class="status">Choose a project folder to begin.</p>
    </section>

    <section id="results" class="panel results">
        <h2>Impact report</h2>
        <p id="changedFileResult"></p>
        <div class="result-section"><h3>Directly affected files</h3><ul id="directFiles"></ul></div>
        <div class="result-section"><h3>Indirectly affected files</h3><ul id="indirectFiles"></ul></div>
        <div class="result-section"><h3>All affected files</h3><ul id="allFiles"></ul></div>
        <div class="result-section"><h3>Related tests</h3><ul id="testFiles"></ul></div>
    </section>

    <section id="aiPanel" class="panel results">
        <h2>🤖 AI Explanation</h2>
        <p class="subtitle">Generated locally by Qwen3 8B through Ollama.</p>
        <div id="aiExplanation" class="ai-box"></div>
    </section>
    <p class="footer">ChangeGuard 2.0 · FastAPI · NetworkX · Ollama</p>
</main>

<script>
async function loadProject() {
    const button = document.getElementById("loadButton");
    const projectStatus = document.getElementById("projectStatus");
    const analyzeButton = document.getElementById("analyzeButton");
    const changedFile = document.getElementById("changedFile");
    const projectPath = document.getElementById("projectPath").value.trim();

    if (!projectPath) {
        projectStatus.textContent = "Please enter the full path to a project folder.";
        return;
    }

    button.disabled = true;
    analyzeButton.disabled = true;
    changedFile.disabled = true;
    projectStatus.textContent = "Scanning the folder for Python files...";
    document.getElementById("results").style.display = "none";
    document.getElementById("aiPanel").style.display = "none";

    try {
        const response = await fetch("/project-files", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({project_path: projectPath})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not load project.");

        changedFile.replaceChildren();
        data.files.forEach(file => {
            const option = document.createElement("option");
            option.value = file.path;
            option.textContent = file.relative_path;
            changedFile.appendChild(option);
        });

        changedFile.disabled = false;
        analyzeButton.disabled = data.files.length === 0;
        projectStatus.textContent =
            "Project loaded successfully.\nFolder: " + data.project_path +
            "\nPython files found: " + data.files.length;
        document.getElementById("status").textContent =
            "Select a Python file and click Analyze impact.";
    } catch (error) {
        changedFile.replaceChildren();
        const option = document.createElement("option");
        option.textContent = "Could not load project";
        option.value = "";
        changedFile.appendChild(option);
        projectStatus.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
}

async function analyzeImpact() {
    const button = document.getElementById("analyzeButton");
    const status = document.getElementById("status");
    const changedFile = document.getElementById("changedFile").value;
    const results = document.getElementById("results");
    const aiPanel = document.getElementById("aiPanel");

    if (!changedFile) {
        status.textContent = "Please load a project and select a Python file first.";
        return;
    }

    button.disabled = true;
    status.textContent = "Analyzing dependencies...";
    results.style.display = "none";
    aiPanel.style.display = "none";

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({changed_file: changedFile})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Analysis failed.");

        document.getElementById("changedFileResult").textContent =
            "Changed file: " + data.changed_file;
        renderList("directFiles", data.directly_affected);
        renderList("indirectFiles", data.indirectly_affected);
        renderList("allFiles", data.all_affected);
        renderList("testFiles", data.related_tests);
        results.style.display = "block";
        status.textContent = "Dependency analysis completed. Generating AI explanation...";

        const aiResponse = await fetch("/explain", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({changed_file: changedFile})
        });
        const aiData = await aiResponse.json();
        if (!aiResponse.ok) throw new Error(aiData.detail || "AI explanation failed.");

        document.getElementById("aiExplanation").textContent = aiData.explanation;
        aiPanel.style.display = "block";
        status.textContent = "Dependency analysis and AI explanation completed.";
    } catch (error) {
        status.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
}

function renderList(elementId, files) {
    const list = document.getElementById(elementId);
    list.replaceChildren();
    if (!files || files.length === 0) {
        const item = document.createElement("li");
        item.textContent = "No files found.";
        item.className = "empty";
        list.appendChild(item);
        return;
    }
    files.forEach(file => {
        const item = document.createElement("li");
        item.textContent = file;
        list.appendChild(item);
    });
}

window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("projectPath").value = __DEFAULT_PROJECT_PATH__;
    loadProject();
});
</script>
</body>
</html>
""".replace("__DEFAULT_PROJECT_PATH__", __import__("json").dumps(str(DEFAULT_PROJECT_PATH)))


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/project-files")
def get_project_files(request: ProjectRequest):
    global PROJECT_PATH

    candidate = Path(request.project_path).expanduser().resolve()
    if not candidate.exists():
        raise HTTPException(status_code=400, detail="That folder does not exist. Check the path and try again.")
    if not candidate.is_dir():
        raise HTTPException(status_code=400, detail="The path must point to a folder, not a file.")

    try:
        python_files = scan_python_files(str(candidate))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not scan that folder: {error}") from error

    if not python_files:
        raise HTTPException(status_code=400, detail="No Python files were found in that folder.")

    PROJECT_PATH = candidate
    files = []
    for file_path in sorted(p.resolve() for p in python_files):
        try:
            relative_path = file_path.relative_to(candidate).as_posix()
        except ValueError:
            relative_path = file_path.name
        files.append({"path": str(file_path), "relative_path": relative_path})

    return {"project_path": str(candidate), "files": files}


@app.post("/analyze")
def analyze_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))
    try:
        return analyze_impact(graph, request.changed_file)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/explain")
def explain_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))
    try:
        impact = analyze_impact(graph, request.changed_file)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    prompt = f"""
You are ChangeGuard, a Python code-change impact analysis assistant.
Explain this impact report to a beginner.

Changed file: {impact.get("changed_file", request.changed_file)}
Directly affected files: {impact.get("directly_affected", [])}
Indirectly affected files: {impact.get("indirectly_affected", [])}
All affected files: {impact.get("all_affected", [])}
Related tests: {impact.get("related_tests", [])}

Provide:
1. What the changed file is likely responsible for.
2. Why the listed files may be affected.
3. Which tests should be run and why.
4. A short recommended next step.

Use simple language and concise bullet points.
Only use the supplied report. Do not claim you inspected code that was not provided.
Do not invent functions or dependencies.
"""
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2},
        )
        explanation = response["message"]["content"].strip()
        return {
            "changed_file": request.changed_file,
            "model": MODEL_NAME,
            "explanation": explanation,
        }
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not generate the AI explanation. Check that Ollama is running "
                f"and model '{MODEL_NAME}' is installed. Details: {error}"
            ),
        ) from error
