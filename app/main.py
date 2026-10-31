from pathlib import Path
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.test_runner import run_related_tests
from app.git_impact_analyzer import analyze_git_impact
from app.git_impact_analyzer import analyze_working_tree_impact


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

class GitImpactRequest(BaseModel):
    project_path: str
    base_ref: str
    compare_ref: str

class WorkingTreeRequest(BaseModel):
    project_path: str

class RunTestsRequest(BaseModel):
    project_path: str
    related_tests: list[str]

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
        .container { max-width: 1100px; margin: auto; }
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
        .graph-wrap { width: 100%; overflow: auto; background: #0b1220; border: 1px solid #334155; border-radius: 10px; padding: 12px; }
        #dependencyGraph { display: block; min-width: 100%; }
        .legend { display: flex; flex-wrap: wrap; gap: 14px; color: #cbd5e1; font-size: 13px; margin: 12px 0; }
        .legend span { display: inline-flex; align-items: center; gap: 6px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .graph-help { color: #94a3b8; font-size: 13px; line-height: 1.5; }
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
    <h2>Git Analysis</h2>
    <p class="subtitle">
        Compare two Git versions to find changed files
        and identify potentially affected files and tests.
    </p>

    <label for="gitBaseRef">Base Git reference</label>
    <input id="gitBaseRef" type="text" value="HEAD~1">

    <label for="gitCompareRef">Compare against</label>
    <input id="gitCompareRef" type="text" value="HEAD">

    <button id="gitAnalyzeButton" onclick="analyzeGitChanges()">
        Analyze Git Changes
    </button>
    <button id="runTestsButton" onclick="runRelatedTests()">
        Run Related Tests
    </button>
    <div id="testResults"></div>
    
    <p id="gitStatus" class="status">
        Enter two Git references and start the analysis.
    </p>

    <div id="gitResults" class="results">
        <div class="result-section">
            <h3>Added files</h3>
            <ul id="gitAdded"></ul>
        </div>
        
        <div class="result-section">
            <h3>Change Risk Assessment</h3>
            <p id="gitRisk">Risk assessment will appear here.</p>
            <p id="gitRiskFactors"></p>
        </div>

        <div class="result-section">
            <h3>Modified files</h3>
            <ul id="gitModified"></ul>
        </div>
        <div class="result-section">
            <h3>Deleted files</h3>
            <ul id="gitDeleted"></ul>
        </div>
        <div class="result-section">
            <h3>Potentially affected files</h3>
            <ul id="gitAffected"></ul>
        </div>
        <div class="result-section">
            <h3>Related tests</h3>
            <ul id="gitTests"></ul>
        </div>
        
    </div>
</section>
    
<section class="panel">
    <h2>Working Tree Analysis</h2>
    <p class="subtitle">
        Analyze local Python changes in your project compared with HEAD,
        including staged, unstaged, and untracked files.
    </p>

    <button id="workingTreeButton" onclick="analyzeWorkingTree()">
        Analyze Working Tree
    </button>

    <p id="workingTreeStatus" class="status">
        Click the button to analyze your local changes.
    </p>

    <div id="workingTreeResults" class="results">
        <div class="result-section">
            <h3>Change Risk Assessment</h3>
            <p id="wtRisk">Risk assessment will appear here.</p>
            <p id="wtRiskFactors"></p>
        </div>
        <div class="result-section">
            <h3>Added files</h3>
            <ul id="wtAdded"></ul>
        </div>
        <div class="result-section">
            <h3>Modified files</h3>
            <ul id="wtModified"></ul>
        </div>
        <div class="result-section">
            <h3>Deleted files</h3>
            <ul id="wtDeleted"></ul>
        </div>
        <div class="result-section">
            <h3>Potentially affected files</h3>
            <ul id="wtAffected"></ul>
        </div>
        <div class="result-section">
            <h3>Related tests</h3>
            <ul id="wtTests"></ul>
        </div>
    </div>
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

    <section id="graphPanel" class="panel results">
        <h2>🕸️ Visual dependency graph</h2>
        <p class="graph-help">Focused impact view: shows the changed file and detected direct/indirect impacts. Arrows point from a dependency to the file that uses it.</p>
        <div class="legend">
            <span><i class="dot" style="background:#ef4444"></i>Changed file</span>
            <span><i class="dot" style="background:#3b82f6"></i>Direct impact</span>
            <span><i class="dot" style="background:#22c55e"></i>Indirect impact</span>
            <span><i class="dot" style="background:#64748b"></i>Other file</span>
            <span><i class="dot" style="background:#6d28d9"></i>Related test</span>
        </div>
        <div class="graph-wrap"><svg id="dependencyGraph" role="img" aria-label="Python file dependency graph"></svg></div>
        <p id="graphStatus" class="graph-help"></p>
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
    window.latestRelatedTests = [];
    const results = document.getElementById("results");
    const aiPanel = document.getElementById("aiPanel");
    const graphPanel = document.getElementById("graphPanel");

    if (!changedFile) {
        status.textContent = "Please load a project and select a Python file first.";
        return;
    }

    button.disabled = true;
    status.textContent = "Analyzing dependencies...";
    results.style.display = "none";
    aiPanel.style.display = "none";
    graphPanel.style.display = "none";

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
        window.latestRelatedTests = data.related_tests || [];
        results.style.display = "block";
        status.textContent = "Dependency analysis completed. Building visual graph...";

        const graphResponse = await fetch("/graph-data", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({changed_file: changedFile})
        });
        const graphData = await graphResponse.json();
        if (!graphResponse.ok) throw new Error(graphData.detail || "Could not build dependency graph.");
        renderDependencyGraph(graphData);
        graphPanel.style.display = "block";
        status.textContent = "Dependency graph ready. Generating AI explanation...";

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

async function analyzeGitChanges() {
    const button = document.getElementById("gitAnalyzeButton");
    const status = document.getElementById("gitStatus");
    const results = document.getElementById("gitResults");

    const projectPath = document.getElementById("projectPath").value.trim();
    const baseRef = document.getElementById("gitBaseRef").value.trim();
    const compareRef = document.getElementById("gitCompareRef").value.trim();

    if (!projectPath || !baseRef || !compareRef) {
        status.textContent = "Enter the project path and both Git references.";
        return;
    }

    button.disabled = true;
    results.style.display = "none";
    status.textContent = "Comparing Git versions and analyzing impact...";

    try {
        const response = await fetch("/git-analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                project_path: projectPath,
                base_ref: baseRef,
                compare_ref: compareRef
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Git analysis failed.");
        }

        renderList("gitAdded", data.added);
        renderList("gitModified", data.modified);
        renderList("gitDeleted", data.deleted);
        renderList("gitAffected", data.all_affected);
        renderList("gitTests", data.related_tests);
        
const risk = data.risk;

document.getElementById("gitRisk").textContent =
    risk ? `${risk.score}/100 — ${risk.level} Risk` : "Risk unavailable";

document.getElementById("gitRiskFactors").textContent = risk
    ? `Changed lines: ${risk.factors.changed_lines} | ` +
      `Affected files: ${risk.factors.affected_files} | ` +
      `Related tests found: ${risk.factors.related_tests_found}`
    : "";

        results.style.display = "block";
        status.textContent =
            `Git analysis completed. ${data.total_changed} changed file(s) detected.`;

    } catch (error) {
        status.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
}

async function analyzeWorkingTree() {
    const button = document.getElementById("workingTreeButton");
    const status = document.getElementById("workingTreeStatus");
    const results = document.getElementById("workingTreeResults");

    const projectPath = document.getElementById("projectPath").value.trim();

    if (!projectPath) {
        status.textContent = "Please load a project folder first.";
        return;
    }

    button.disabled = true;
    results.style.display = "none";
    status.textContent = "Analyzing local Python changes...";

    try {
        const response = await fetch("/working-tree-analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                project_path: projectPath
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Working tree analysis failed.");
        }

        renderList("wtAdded", data.added);
        renderList("wtModified", data.modified);
        renderList("wtDeleted", data.deleted);
        renderList("wtAffected", data.all_affected);
        renderList("wtTests", data.related_tests);

        const risk = data.risk;

        document.getElementById("wtRisk").textContent =
            risk ? `${risk.score}/100 — ${risk.level} Risk`
                 : "Risk unavailable";

        document.getElementById("wtRiskFactors").textContent = risk
            ? `Changed lines: ${risk.factors.changed_lines} | ` +
              `Affected files: ${risk.factors.affected_files} | ` +
              `Related tests found: ${risk.factors.related_tests_found}`
            : "";

        results.style.display = "block";
        status.textContent =
            `Working tree analysis completed. ${data.total_changed} changed file(s) detected.`;

    } catch (error) {
        status.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
}

function renderDependencyGraph(data) {
    const svg = document.getElementById("dependencyGraph");
    const graphStatus = document.getElementById("graphStatus");
    svg.replaceChildren();

    const nodes = data.nodes || [];
    const edges = data.edges || [];
    if (!nodes.length) {
        graphStatus.textContent = "No dependency nodes were returned.";
        return;
    }

    const NS = "http://www.w3.org/2000/svg";
    const make = (tag, attrs = {}) => {
        const el = document.createElementNS(NS, tag);
        Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
        return el;
    };
    const nodeByPath = new Map(nodes.map(node => [node.path, node]));
    const children = new Map(nodes.map(node => [node.path, []]));
    edges.forEach(edge => {
        if (children.has(edge.source)) children.get(edge.source).push(edge.target);
    });

    // Place the changed file first, then each downstream impact level.
    const levels = new Map();
    const queue = [{path: data.changed_file, level: 0}];
    levels.set(data.changed_file, 0);
    for (let i = 0; i < queue.length; i++) {
        const current = queue[i];
        (children.get(current.path) || []).forEach(next => {
            if (!levels.has(next)) {
                levels.set(next, current.level + 1);
                queue.push({path: next, level: current.level + 1});
            }
        });
    }
    const maxLevel = Math.max(0, ...levels.values());
    nodes.forEach(node => { if (!levels.has(node.path)) levels.set(node.path, maxLevel + 1); });
    const groups = new Map();
    nodes.forEach(node => {
        const level = levels.get(node.path);
        if (!groups.has(level)) groups.set(level, []);
        groups.get(level).push(node);
    });
    groups.forEach(group => group.sort((a, b) => a.label.localeCompare(b.label)));

    const nodeW = 210, nodeH = 54, xGap = 34, yGap = 95, pad = 30;
    const maxColumns = Math.max(1, ...Array.from(groups.values(), group => group.length));
    const width = Math.max(650, pad * 2 + maxColumns * (nodeW + xGap) - xGap);
    const height = pad * 2 + (Math.max(...groups.keys()) + 1) * (nodeH + yGap) - yGap;
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const positions = new Map();
    groups.forEach((group, level) => {
        const rowWidth = group.length * nodeW + (group.length - 1) * xGap;
        const startX = Math.max(pad, (width - rowWidth) / 2);
        group.forEach((node, index) => {
            positions.set(node.path, {x: startX + index * (nodeW + xGap), y: pad + level * (nodeH + yGap)});
        });
    });

    // Draw arrows behind the file cards.
    edges.forEach(edge => {
        const from = positions.get(edge.source), to = positions.get(edge.target);
        if (!from || !to) return;
        const path = make("path", {
            d: `M ${from.x + nodeW / 2} ${from.y + nodeH} C ${from.x + nodeW / 2} ${from.y + nodeH + 25}, ${to.x + nodeW / 2} ${to.y - 25}, ${to.x + nodeW / 2} ${to.y}`,
            fill: "none", stroke: "#64748b", "stroke-width": "2", "marker-end": "url(#arrowhead)"
        });
        svg.appendChild(path);
    });
    const defs = make("defs");
    const marker = make("marker", {id: "arrowhead", markerWidth: "8", markerHeight: "8", refX: "6", refY: "3", orient: "auto", markerUnits: "strokeWidth"});
    marker.appendChild(make("path", {d: "M0,0 L0,6 L6,3 z", fill: "#64748b"}));
    defs.appendChild(marker);
    svg.insertBefore(defs, svg.firstChild);

    nodes.forEach(node => {
        const pos = positions.get(node.path);
        const colors = {changed: "#b91c1c", direct: "#1d4ed8", indirect: "#15803d", other: "#334155", test: "#6d28d9"};
        const group = make("g");
        const rect = make("rect", {x: pos.x, y: pos.y, width: nodeW, height: nodeH, rx: "10", fill: colors[node.category] || colors.other, stroke: "#94a3b8", "stroke-width": "1"});
        const name = make("text", {x: pos.x + nodeW / 2, y: pos.y + 22, fill: "#ffffff", "font-size": "13", "font-weight": "600", "text-anchor": "middle"});
        name.textContent = node.label.length > 27 ? "…" + node.label.slice(-26) : node.label;
        const role = make("text", {x: pos.x + nodeW / 2, y: pos.y + 41, fill: "#dbeafe", "font-size": "11", "text-anchor": "middle"});
        role.textContent = ({changed: "Changed file", direct: "Direct impact", indirect: "Indirect impact", other: "Other file", test: "Related test"})[node.category] || "Other file";
        group.append(rect, name, role);
        const title = make("title"); title.textContent = node.path; group.appendChild(title);
        svg.appendChild(group);
    });
    graphStatus.textContent = `${nodes.length} relevant files · ${edges.length} dependency connections. Unrelated files are hidden to keep the impact chain readable. Hover over a file card to see its full path.`;
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

async function runRelatedTests() {
    const projectPath = document.getElementById("projectPath").value.trim();
    const resultsDiv = document.getElementById("testResults");
    const button = document.getElementById("runTestsButton");

    if (!projectPath) {
        resultsDiv.textContent = "Please select a project folder first.";
        return;
    }

    button.disabled = true;
    resultsDiv.textContent = "Running related tests...";

    try {
        const response = await fetch("/run-related-tests", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                project_path: projectPath,
                related_tests: window.latestRelatedTests || []
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "The test request failed.");
        }

        resultsDiv.replaceChildren();

        const heading = document.createElement("h3");
        heading.textContent = "Test status: " + result.status;
        resultsDiv.appendChild(heading);

        const summary = document.createElement("p");
        summary.textContent = result.message;
        resultsDiv.appendChild(summary);

        const details = document.createElement("p");
        details.textContent =
            "Test files: " + result.tests_discovered +
            " | Duration: " + result.duration_seconds + " seconds";
        resultsDiv.appendChild(details);

        const output = document.createElement("pre");
        output.textContent = result.output || "No test output.";
        resultsDiv.appendChild(output);

    } catch (error) {
        resultsDiv.textContent = "Could not run tests: " + error.message;
    } finally {
        button.disabled = false;
    }
}

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


@app.post("/graph-data")
def get_graph_data(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))
    try:
        impact = analyze_impact(graph, request.changed_file)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    # Normalize all file references to the same absolute-path format used by
    # graph_builder. Impact reports may contain absolute paths, relative paths,
    # or filenames, depending on the analyzer implementation.
    graph_paths = {str(Path(raw).resolve()) for raw in graph.nodes}
    path_by_relative = {}
    path_by_name = {}
    for raw in graph.nodes:
        absolute = str(Path(raw).resolve())
        try:
            relative = Path(absolute).relative_to(PROJECT_PATH.resolve()).as_posix()
            path_by_relative[relative] = absolute
        except ValueError:
            pass
        path_by_name.setdefault(Path(absolute).name, []).append(absolute)

    def normalize_path(value):
        candidate = Path(str(value)).expanduser()
        if candidate.is_absolute():
            resolved = str(candidate.resolve())
            if resolved in graph_paths:
                return resolved
        else:
            relative = candidate.as_posix().replace('\\', '/')
            if relative in path_by_relative:
                return path_by_relative[relative]
            resolved = str((PROJECT_PATH / candidate).resolve())
            if resolved in graph_paths:
                return resolved
            matches = path_by_name.get(candidate.name, [])
            if len(matches) == 1:
                return matches[0]
        return None

    changed = normalize_path(request.changed_file)
    if changed is None:
        raise HTTPException(status_code=404, detail="The selected file was not found in the dependency graph.")

    # Use the dependency graph itself to find every downstream file reachable
    # from the changed file. This ensures branches are not omitted just because
    # the impact report uses a different path format or misses a transitive file.
    related_tests = {p for value in impact.get("related_tests", []) if (p := normalize_path(value))}
    levels = {changed: 0}
    queue = [changed]
    for current in queue:
        for dependent in graph.successors(current):
            dependent_path = str(Path(dependent).resolve())
            if dependent_path not in levels:
                levels[dependent_path] = levels[current] + 1
                queue.append(dependent_path)

    direct = {path for path, level in levels.items() if level == 1}
    indirect = {path for path, level in levels.items() if level > 1}
    # Keep related tests in the view even if they are discovered by test-name
    # matching rather than an import edge.
    visible_paths = set(levels) | related_tests

    nodes = []
    for file_path in sorted(visible_paths):
        try:
            label = Path(file_path).relative_to(PROJECT_PATH.resolve()).as_posix()
        except ValueError:
            label = Path(file_path).name
        if file_path == changed:
            category = "changed"
        elif file_path in direct:
            category = "direct"
        elif file_path in indirect:
            category = "indirect"
        else:
            category = "test"
        nodes.append({"path": file_path, "label": label, "category": category})

    # Preserve the actual dependency edges detected by the graph builder.
    edges = [
        {"source": str(Path(source).resolve()), "target": str(Path(target).resolve())}
        for source, target in graph.edges
        if str(Path(source).resolve()) in visible_paths
        and str(Path(target).resolve()) in visible_paths
    ]
    return {"changed_file": changed, "nodes": nodes, "edges": edges}


@app.post("/analyze")
def analyze_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))
    try:
        # return analyze_impact(graph, request.changed_file)
        return analyze_impact(
        graph,
        request.changed_file,
        project_root=str(PROJECT_PATH),
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/explain")
def explain_code_change(request: ImpactRequest):
    graph = build_dependency_graph(str(PROJECT_PATH))
    try:
        # impact = analyze_impact(graph, request.changed_file)
        impact = analyze_impact(
        graph,
        request.changed_file,
        project_root=str(PROJECT_PATH),
    )
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


@app.post("/working-tree-analyze")
def analyze_working_tree(request: WorkingTreeRequest):
    try:
        return analyze_working_tree_impact(
            project_path=request.project_path,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

@app.post("/git-analyze")
def analyze_git_changes(request: GitImpactRequest):
    try:
        return analyze_git_impact(
            project_path=request.project_path,
            base_ref=request.base_ref,
            compare_ref=request.compare_ref,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

@app.post("/run-related-tests")
def run_project_related_tests(request: RunTestsRequest):
    project_root = Path(request.project_path).expanduser().resolve()

    if not project_root.exists() or not project_root.is_dir():
        raise HTTPException(
            status_code=400,
            detail="The selected project folder does not exist.",
        )

    try:
        return run_related_tests(
            project_root=str(project_root),
            related_tests=request.related_tests,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not run related tests: {error}",
        ) from error
