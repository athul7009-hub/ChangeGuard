
from pathlib import Path

import ollama
import os
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.graph_builder import build_dependency_graph
from app.impact_analyzer import analyze_impact


app = FastAPI(
    title="ChangeGuard API",
    description="Analyze the potential impact of Python code changes.",
    version="1.1.0",
)

PROJECT_PATH = Path(__file__).resolve().parent.parent / "sample_project"
MODEL_NAME = "qwen3:8b"


class ImpactRequest(BaseModel):
    changed_file: str


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChangeGuard | Code Impact Analyzer</title>

    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            padding: 35px 20px;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }

        .container { max-width: 850px; margin: auto; }
        h1 { color: #5eead4; margin-bottom: 8px; }
        .subtitle { color: #94a3b8; margin-bottom: 28px; }

        .panel {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
        }

        select, button {
            width: 100%;
            padding: 13px;
            border-radius: 8px;
            font-size: 15px;
        }

        select {
            background: #0f172a;
            color: white;
            border: 1px solid #475569;
            margin-bottom: 15px;
        }

        button {
            background: #14b8a6;
            color: #042f2e;
            border: none;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover { background: #5eead4; }
        button:disabled { opacity: 0.6; cursor: wait; }

        .status {
            color: #94a3b8;
            margin-top: 14px;
            white-space: pre-wrap;
        }

        .results { display: none; }

        .result-section {
            border-top: 1px solid #334155;
            padding-top: 14px;
            margin-top: 14px;
        }

        h2 { font-size: 19px; }

        h3 {
            font-size: 15px;
            color: #5eead4;
        }

        ul { padding-left: 22px; }
        li { margin: 8px 0; }
        .empty { color: #94a3b8; }

        .ai-box {
            white-space: pre-wrap;
            line-height: 1.7;
            overflow-wrap: anywhere;
            color: #e2e8f0;
        }

        .footer {
            text-align: center;
            color: #64748b;
            font-size: 13px;
            margin-top: 24px;
        }
    </style>
</head>

<body>
    <main class="container">
        <h1>🛡️ ChangeGuard</h1>
        <p class="subtitle">
            Understand which files may be affected by a code change.
        </p>

        <section class="panel">
            <h2>Analyze a code change</h2>

            <label for="changedFile">Select a Python file</label>

            <select id="changedFile">
                <option value="calculator.py">calculator.py</option>
                <option value="evaluator.py">evaluator.py</option>
                <option value="pipeline.py">pipeline.py</option>
                <option value="main.py">main.py</option>
                <option value="test_calculator.py">test_calculator.py</option>
            </select>

            <button id="analyzeButton" onclick="analyzeImpact()">
                Analyze impact
            </button>

            <p id="status" class="status">
                Select a file and click Analyze impact.
            </p>
        </section>

        <section id="results" class="panel results">
            <h2>Impact report</h2>
            <p id="changedFileResult"></p>

            <div class="result-section">
                <h3>Directly affected files</h3>
                <ul id="directFiles"></ul>
            </div>

            <div class="result-section">
                <h3>Indirectly affected files</h3>
                <ul id="indirectFiles"></ul>
            </div>

            <div class="result-section">
                <h3>All affected files</h3>
                <ul id="allFiles"></ul>
            </div>

            <div class="result-section">
                <h3>Related tests</h3>
                <ul id="testFiles"></ul>
            </div>
        </section>

        <section id="aiPanel" class="panel results">
            <h2>🤖 AI Explanation</h2>
            <p class="subtitle">
                Explanation generated locally by Qwen3 8B through Ollama.
            </p>
            <div id="aiExplanation" class="ai-box"></div>
        </section>

        <p class="footer">
            ChangeGuard MVP · FastAPI · NetworkX · Ollama
        </p>
    </main>

    <script>
        async function analyzeImpact() {
            const button = document.getElementById("analyzeButton");
            const status = document.getElementById("status");
            const results = document.getElementById("results");
            const aiPanel = document.getElementById("aiPanel");
            const changedFile =
                document.getElementById("changedFile").value;

            button.disabled = true;
            status.textContent = "Analyzing dependencies...";
            results.style.display = "none";
            aiPanel.style.display = "none";

            try {
                const response = await fetch("/analyze", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        changed_file: changedFile
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Analysis failed.");
                }

                document.getElementById("changedFileResult").textContent =
                    "Changed file: " + data.changed_file;

                renderList("directFiles", data.directly_affected);
                renderList("indirectFiles", data.indirectly_affected);
                renderList("allFiles", data.all_affected);
                renderList("testFiles", data.related_tests);

                results.style.display = "block";
                status.textContent = "Dependency analysis completed.";

                status.textContent +=
                    "\\nGenerating AI explanation... This may take a little time.";

                const aiResponse = await fetch("/explain", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        changed_file: changedFile
                    })
                });

                const aiData = await aiResponse.json();

                if (!aiResponse.ok) {
                    throw new Error(
                        aiData.detail || "AI explanation failed."
                    );
                }

                document.getElementById("aiExplanation").textContent =
                    aiData.explanation;

                aiPanel.style.display = "block";
                status.textContent =
                    "Dependency analysis and AI explanation completed.";

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

            files.forEach(function(file) {
                const item = document.createElement("li");
                item.textContent = file;
                list.appendChild(item);
            });
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/analyze")
def analyze_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))

    try:
        return analyze_impact(graph, request.changed_file)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@app.post("/explain")
def explain_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))

    try:
        impact = analyze_impact(graph, request.changed_file)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

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
                "Could not generate the AI explanation. "
                "Check that Ollama is running and the model "
                f"'{MODEL_NAME}' is installed. Details: {error}"
            ),
        ) from error
