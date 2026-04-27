# Autonomous Agents — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the research + planning pipeline — orchestrator dispatches research_agent (Gemini web search → idea.md) then plan_agent (idea.md → architecture.md, stack.md, tasks.json).

**Architecture:** Central orchestrator reads/writes a runtime `tasks.json` tracking pipeline state. Each agent is an independent Python script that calls Gemini CLI via subprocess with `--yolo`, writes output files, and updates task status. Shared utilities handle task state and logging.

**Tech Stack:** Python 3.11+, Gemini CLI (must be installed and on PATH), pytest, subprocess, json, pathlib, logging

---

## File Map

| File | Responsibility |
|---|---|
| `orchestrator.py` | Main entry point. Dispatches agents in sequence, handles retries, halts on blocked. |
| `agents/base_agent.py` | `call_gemini()` wrapper. Used by all agents. |
| `agents/research_agent.py` | Calls Gemini with web search. Writes `output/idea.md`. Updates task status. |
| `agents/plan_agent.py` | Reads `output/idea.md`. Calls Gemini. Writes `output/architecture.md`, `output/stack.md`, `output/tasks.json`. |
| `utils/task_manager.py` | Read/write/update `tasks.json`. Single source of truth for task state. |
| `utils/logger.py` | Returns configured logger writing to `logs/<agent>_<timestamp>.log`. |
| `tasks.json` | Runtime pipeline state. Initialized by orchestrator, updated by agents. |
| `output/` | Directory for agent-generated markdown and json files. |
| `logs/` | Per-agent timestamped log files. |
| `tests/test_task_manager.py` | Unit tests for task_manager. |
| `tests/test_base_agent.py` | Unit tests for call_gemini (mocked subprocess). |
| `tests/test_research_agent.py` | Unit tests for research_agent (mocked Gemini). |
| `tests/test_plan_agent.py` | Unit tests for plan_agent (mocked Gemini). |
| `tests/test_orchestrator.py` | Integration tests for orchestrator Phase 1. |
| `requirements.txt` | Python dependencies. |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `agents/__init__.py`
- Create: `utils/__init__.py`
- Create: `tests/__init__.py`
- Create: `output/.gitkeep`
- Create: `logs/.gitkeep`
- Create: `workspace/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p agents utils tests output logs workspace
touch agents/__init__.py utils/__init__.py tests/__init__.py
touch output/.gitkeep logs/.gitkeep workspace/.gitkeep
```

- [ ] **Step 2: Create requirements.txt**

```
pytest==8.3.5
pytest-mock==3.14.0
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: installs pytest and pytest-mock without errors.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt agents/__init__.py utils/__init__.py tests/__init__.py output/.gitkeep logs/.gitkeep workspace/.gitkeep
git commit -m "chore: project scaffold — directories and dependencies"
```

---

## Task 2: task_manager utility

**Files:**
- Create: `utils/task_manager.py`
- Create: `tests/test_task_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_task_manager.py`:

```python
import json
import pytest
from pathlib import Path
from utils.task_manager import TaskManager


@pytest.fixture
def tmp_tasks(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    data = {
        "tasks": [
            {
                "id": "task_001",
                "type": "research",
                "status": "pending",
                "description": "Research market ideas",
                "depends_on": [],
                "output_file": "output/idea.md",
                "retries": 0,
                "error": None
            }
        ]
    }
    tasks_file.write_text(json.dumps(data))
    return tasks_file


def test_load_tasks(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    tasks = tm.load()
    assert len(tasks) == 1
    assert tasks[0]["id"] == "task_001"


def test_update_status(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    tm.update_status("task_001", "in_progress")
    tasks = tm.load()
    assert tasks[0]["status"] == "in_progress"


def test_update_status_with_error(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    tm.update_status("task_001", "failed", error="timeout")
    tasks = tm.load()
    assert tasks[0]["status"] == "failed"
    assert tasks[0]["error"] == "timeout"


def test_increment_retries(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    tm.increment_retries("task_001")
    tasks = tm.load()
    assert tasks[0]["retries"] == 1


def test_get_next_ready_task(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    task = tm.get_next_ready_task()
    assert task["id"] == "task_001"


def test_get_next_ready_task_respects_depends_on(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    data = {
        "tasks": [
            {"id": "t1", "type": "planning", "status": "pending", "depends_on": ["t2"],
             "description": "", "output_file": "", "retries": 0, "error": None},
            {"id": "t2", "type": "research", "status": "pending", "depends_on": [],
             "description": "", "output_file": "", "retries": 0, "error": None}
        ]
    }
    tasks_file.write_text(json.dumps(data))
    tm = TaskManager(tasks_file)
    task = tm.get_next_ready_task()
    assert task["id"] == "t2"


def test_all_done(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    assert not tm.all_done()
    tm.update_status("task_001", "done")
    assert tm.all_done()


def test_any_blocked(tmp_tasks):
    tm = TaskManager(tmp_tasks)
    assert not tm.any_blocked()
    tm.update_status("task_001", "blocked")
    assert tm.any_blocked()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_task_manager.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'utils.task_manager'`

- [ ] **Step 3: Implement task_manager.py**

Create `utils/task_manager.py`:

```python
import json
from pathlib import Path


class TaskManager:
    def __init__(self, tasks_file: Path):
        self.tasks_file = Path(tasks_file)

    def load(self) -> list[dict]:
        data = json.loads(self.tasks_file.read_text())
        return data["tasks"]

    def _save(self, tasks: list[dict]):
        self.tasks_file.write_text(json.dumps({"tasks": tasks}, indent=2))

    def update_status(self, task_id: str, status: str, error: str | None = None):
        tasks = self.load()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = status
                if error is not None:
                    task["error"] = error
                break
        self._save(tasks)

    def increment_retries(self, task_id: str):
        tasks = self.load()
        for task in tasks:
            if task["id"] == task_id:
                task["retries"] += 1
                break
        self._save(tasks)

    def get_next_ready_task(self) -> dict | None:
        tasks = self.load()
        done_ids = {t["id"] for t in tasks if t["status"] == "done"}
        for task in tasks:
            if task["status"] == "pending":
                if all(dep in done_ids for dep in task["depends_on"]):
                    return task
        return None

    def all_done(self) -> bool:
        return all(t["status"] == "done" for t in self.load())

    def any_blocked(self) -> bool:
        return any(t["status"] == "blocked" for t in self.load())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_task_manager.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add utils/task_manager.py tests/test_task_manager.py
git commit -m "feat: add TaskManager utility for task state management"
```

---

## Task 3: logger utility

**Files:**
- Create: `utils/logger.py`

- [ ] **Step 1: Create logger.py**

```python
import logging
from datetime import datetime
from pathlib import Path


def get_logger(agent_name: str, logs_dir: str = "logs") -> logging.Logger:
    Path(logs_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(logs_dir) / f"{agent_name}_{timestamp}.log"

    logger = logging.getLogger(f"{agent_name}_{timestamp}")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
```

- [ ] **Step 2: Verify manually**

```bash
python -c "from utils.logger import get_logger; log = get_logger('test'); log.info('ok')"
ls logs/
```

Expected: `logs/test_<timestamp>.log` file created.

- [ ] **Step 3: Commit**

```bash
git add utils/logger.py
git commit -m "feat: add get_logger utility for per-agent timestamped logs"
```

---

## Task 4: base_agent — call_gemini wrapper

**Files:**
- Create: `agents/base_agent.py`
- Create: `tests/test_base_agent.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_base_agent.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from agents.base_agent import call_gemini


def test_call_gemini_returns_stdout():
    mock_result = MagicMock()
    mock_result.stdout = "  gemini output  "
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result) as mock_run:
        result = call_gemini("test prompt")
        assert result == "gemini output"
        mock_run.assert_called_once_with(
            ["gemini", "-p", "test prompt", "--yolo"],
            capture_output=True, text=True, timeout=120
        )


def test_call_gemini_without_modifications():
    mock_result = MagicMock()
    mock_result.stdout = "output"
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result) as mock_run:
        call_gemini("prompt", allow_modifications=False)
        cmd = mock_run.call_args[0][0]
        assert "--yolo" not in cmd


def test_call_gemini_raises_on_empty_output():
    mock_result = MagicMock()
    mock_result.stdout = "   "
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result):
        with pytest.raises(ValueError, match="empty output"):
            call_gemini("prompt")


def test_call_gemini_raises_on_nonzero_returncode():
    mock_result = MagicMock()
    mock_result.stdout = "some output"
    mock_result.returncode = 1
    mock_result.stderr = "gemini error"

    with patch("agents.base_agent.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="gemini error"):
            call_gemini("prompt")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_base_agent.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'agents.base_agent'`

- [ ] **Step 3: Implement base_agent.py**

Create `agents/base_agent.py`:

```python
import subprocess


def call_gemini(prompt: str, allow_modifications: bool = True, timeout: int = 120) -> str:
    cmd = ["gemini", "-p", prompt]
    if allow_modifications:
        cmd.append("--yolo")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gemini exited with non-zero status")

    output = result.stdout.strip()
    if not output:
        raise ValueError("gemini returned empty output")

    return output
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_base_agent.py -v
```

Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agents/base_agent.py tests/test_base_agent.py
git commit -m "feat: add call_gemini base agent wrapper with --yolo support"
```

---

## Task 5: research_agent

**Files:**
- Create: `agents/research_agent.py`
- Create: `tests/test_research_agent.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_research_agent.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from agents.research_agent import ResearchAgent


@pytest.fixture
def setup(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    data = {
        "tasks": [
            {
                "id": "task_research",
                "type": "research",
                "status": "pending",
                "description": "Research market ideas",
                "depends_on": [],
                "output_file": str(output_dir / "idea.md"),
                "retries": 0,
                "error": None
            }
        ]
    }
    tasks_file.write_text(json.dumps(data))
    return tasks_file, output_dir


def test_research_agent_writes_idea_md(setup):
    tasks_file, output_dir = setup
    gemini_output = "# Best SaaS Idea\n\nAutomated invoice processing for SMBs."

    with patch("agents.research_agent.call_gemini", return_value=gemini_output):
        agent = ResearchAgent(tasks_file=tasks_file)
        agent.run(task_id="task_research")

    idea_file = output_dir / "idea.md"
    assert idea_file.exists()
    assert "SaaS" in idea_file.read_text()


def test_research_agent_marks_task_done(setup):
    tasks_file, output_dir = setup

    with patch("agents.research_agent.call_gemini", return_value="# Idea\nContent."):
        agent = ResearchAgent(tasks_file=tasks_file)
        agent.run(task_id="task_research")

    data = json.loads(tasks_file.read_text())
    task = next(t for t in data["tasks"] if t["id"] == "task_research")
    assert task["status"] == "done"


def test_research_agent_marks_failed_on_error(setup):
    tasks_file, output_dir = setup

    with patch("agents.research_agent.call_gemini", side_effect=ValueError("empty output")):
        agent = ResearchAgent(tasks_file=tasks_file)
        with pytest.raises(ValueError):
            agent.run(task_id="task_research")

    data = json.loads(tasks_file.read_text())
    task = next(t for t in data["tasks"] if t["id"] == "task_research")
    assert task["status"] == "failed"
    assert "empty output" in task["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_research_agent.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'agents.research_agent'`

- [ ] **Step 3: Implement research_agent.py**

Create `agents/research_agent.py`:

```python
from pathlib import Path
from agents.base_agent import call_gemini
from utils.task_manager import TaskManager
from utils.logger import get_logger

RESEARCH_PROMPT = """
You are a market research analyst. Use web search to find current market trends and gaps.

Research the following:
1. Top 5 emerging SaaS/software niches with high demand and low competition in 2024-2026
2. For each niche: problem it solves, target audience, monetization model, competitor landscape
3. Choose the single best opportunity and justify your choice with data

Output a markdown document with:
- # Chosen Idea: [Name]
- ## Problem Statement
- ## Target Market
- ## Why Now (market timing)
- ## Monetization Model
- ## Competitive Landscape
- ## Key Features (MVP, 5-7 items)
- ## Tech Stack Recommendation
"""


class ResearchAgent:
    def __init__(self, tasks_file: Path):
        self.tm = TaskManager(Path(tasks_file))
        self.logger = get_logger("research_agent")

    def run(self, task_id: str):
        tasks = self.tm.load()
        task = next(t for t in tasks if t["id"] == task_id)
        output_file = Path(task["output_file"])

        self.tm.update_status(task_id, "in_progress")
        self.logger.info(f"Starting research for task {task_id}")

        try:
            result = call_gemini(RESEARCH_PROMPT)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(result)
            self.logger.info(f"idea.md written to {output_file}")
            self.tm.update_status(task_id, "done")
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            self.tm.update_status(task_id, "failed", error=str(e))
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_research_agent.py -v
```

Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agents/research_agent.py tests/test_research_agent.py
git commit -m "feat: add research_agent — Gemini web search to idea.md"
```

---

## Task 6: plan_agent

**Files:**
- Create: `agents/plan_agent.py`
- Create: `tests/test_plan_agent.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_plan_agent.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from agents.plan_agent import PlanAgent


MOCK_ARCHITECTURE = "# Architecture\n\nMicroservices with FastAPI backend."
MOCK_STACK = "# Stack\n\nPython, FastAPI, PostgreSQL, React."
MOCK_TASKS = json.dumps({
    "tasks": [
        {
            "id": "task_001",
            "type": "code",
            "status": "pending",
            "description": "Create FastAPI app scaffold",
            "depends_on": [],
            "output_file": "workspace/main.py",
            "retries": 0,
            "error": None
        }
    ]
})


@pytest.fixture
def setup(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    idea_file = output_dir / "idea.md"
    idea_file.write_text("# Idea\nAutomated invoicing SaaS.")

    data = {
        "tasks": [
            {
                "id": "task_planning",
                "type": "planning",
                "status": "pending",
                "description": "Generate architecture, stack and task breakdown",
                "depends_on": ["task_research"],
                "output_file": str(output_dir / "tasks.json"),
                "retries": 0,
                "error": None
            }
        ]
    }
    tasks_file.write_text(json.dumps(data))
    return tasks_file, output_dir


def test_plan_agent_writes_output_files(setup):
    tasks_file, output_dir = setup

    outputs = [MOCK_ARCHITECTURE, MOCK_STACK, MOCK_TASKS]
    with patch("agents.plan_agent.call_gemini", side_effect=outputs):
        agent = PlanAgent(tasks_file=tasks_file, output_dir=output_dir)
        agent.run(task_id="task_planning")

    assert (output_dir / "architecture.md").exists()
    assert (output_dir / "stack.md").exists()
    assert (output_dir / "tasks.json").exists()


def test_plan_agent_tasks_json_is_valid(setup):
    tasks_file, output_dir = setup

    outputs = [MOCK_ARCHITECTURE, MOCK_STACK, MOCK_TASKS]
    with patch("agents.plan_agent.call_gemini", side_effect=outputs):
        agent = PlanAgent(tasks_file=tasks_file, output_dir=output_dir)
        agent.run(task_id="task_planning")

    content = json.loads((output_dir / "tasks.json").read_text())
    assert "tasks" in content
    assert len(content["tasks"]) > 0


def test_plan_agent_marks_task_done(setup):
    tasks_file, output_dir = setup

    outputs = [MOCK_ARCHITECTURE, MOCK_STACK, MOCK_TASKS]
    with patch("agents.plan_agent.call_gemini", side_effect=outputs):
        agent = PlanAgent(tasks_file=tasks_file, output_dir=output_dir)
        agent.run(task_id="task_planning")

    data = json.loads(tasks_file.read_text())
    task = next(t for t in data["tasks"] if t["id"] == "task_planning")
    assert task["status"] == "done"


def test_plan_agent_marks_failed_on_invalid_tasks_json(setup):
    tasks_file, output_dir = setup

    outputs = [MOCK_ARCHITECTURE, MOCK_STACK, "not valid json at all"]
    with patch("agents.plan_agent.call_gemini", side_effect=outputs):
        agent = PlanAgent(tasks_file=tasks_file, output_dir=output_dir)
        with pytest.raises(ValueError):
            agent.run(task_id="task_planning")

    data = json.loads(tasks_file.read_text())
    task = next(t for t in data["tasks"] if t["id"] == "task_planning")
    assert task["status"] == "failed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_plan_agent.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'agents.plan_agent'`

- [ ] **Step 3: Implement plan_agent.py**

Create `agents/plan_agent.py`:

```python
import json
import re
from pathlib import Path
from agents.base_agent import call_gemini
from utils.task_manager import TaskManager
from utils.logger import get_logger

ARCHITECTURE_PROMPT = """
Based on the following product idea, generate a software architecture document in markdown.

{idea}

Include:
- ## Overview (2-3 sentences)
- ## Components (list each service/module with one-line description)
- ## Data Flow (how data moves between components)
- ## Key Design Decisions (why this architecture fits the product)
"""

STACK_PROMPT = """
Based on the following product idea and architecture, recommend a tech stack in markdown.

{idea}

{architecture}

Include:
- ## Backend
- ## Frontend
- ## Database
- ## Infrastructure
- ## Why This Stack (brief justification per choice)
"""

TASKS_PROMPT = """
Based on the following product idea, architecture, and stack, generate a JSON task list for autonomous coding agents.

{idea}

{architecture}

{stack}

Return ONLY valid JSON (no markdown, no explanation) with this exact schema:
{{
  "tasks": [
    {{
      "id": "task_001",
      "type": "code",
      "status": "pending",
      "description": "description of what to build",
      "depends_on": [],
      "output_file": "workspace/path/to/file.py",
      "retries": 0,
      "error": null
    }}
  ]
}}

Rules:
- Break down into small, single-file tasks
- Set depends_on to task ids that must complete first
- output_file must be a path inside workspace/
- Generate 8-15 tasks covering the full MVP
"""


def _extract_json(text: str) -> dict:
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError(f"No JSON found in output: {text[:200]}")
    return json.loads(match.group())


class PlanAgent:
    def __init__(self, tasks_file: Path, output_dir: Path = Path("output")):
        self.tm = TaskManager(Path(tasks_file))
        self.output_dir = Path(output_dir)
        self.logger = get_logger("plan_agent")

    def run(self, task_id: str):
        self.tm.update_status(task_id, "in_progress")
        self.logger.info(f"Starting planning for task {task_id}")

        try:
            idea = (self.output_dir / "idea.md").read_text()

            architecture = call_gemini(ARCHITECTURE_PROMPT.format(idea=idea))
            (self.output_dir / "architecture.md").write_text(architecture)
            self.logger.info("architecture.md written")

            stack = call_gemini(STACK_PROMPT.format(idea=idea, architecture=architecture))
            (self.output_dir / "stack.md").write_text(stack)
            self.logger.info("stack.md written")

            tasks_raw = call_gemini(TASKS_PROMPT.format(
                idea=idea, architecture=architecture, stack=stack
            ))
            tasks_data = _extract_json(tasks_raw)
            tasks_out = self.output_dir / "tasks.json"
            tasks_out.write_text(json.dumps(tasks_data, indent=2))
            self.logger.info(f"tasks.json written with {len(tasks_data['tasks'])} tasks")

            self.tm.update_status(task_id, "done")

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            self.tm.update_status(task_id, "failed", error=str(e))
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plan_agent.py -v
```

Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agents/plan_agent.py tests/test_plan_agent.py
git commit -m "feat: add plan_agent — generates architecture.md, stack.md, tasks.json"
```

---

## Task 7: orchestrator — Phase 1

**Files:**
- Create: `orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_orchestrator.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from orchestrator import Orchestrator, init_pipeline_tasks


@pytest.fixture
def tmp_env(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return tmp_path, tasks_file, output_dir


def test_init_pipeline_tasks_creates_tasks_json(tmp_env):
    tmp_path, tasks_file, output_dir = tmp_env
    init_pipeline_tasks(tasks_file, output_dir)
    data = json.loads(tasks_file.read_text())
    ids = [t["id"] for t in data["tasks"]]
    assert "task_research" in ids
    assert "task_planning" in ids


def test_init_pipeline_tasks_planning_depends_on_research(tmp_env):
    tmp_path, tasks_file, output_dir = tmp_env
    init_pipeline_tasks(tasks_file, output_dir)
    data = json.loads(tasks_file.read_text())
    planning = next(t for t in data["tasks"] if t["id"] == "task_planning")
    assert "task_research" in planning["depends_on"]


def test_orchestrator_runs_research_then_plan(tmp_env):
    tmp_path, tasks_file, output_dir = tmp_env
    init_pipeline_tasks(tasks_file, output_dir)

    with patch("orchestrator.ResearchAgent") as MockResearch, \
         patch("orchestrator.PlanAgent") as MockPlan:

        mock_research_inst = MagicMock()
        mock_plan_inst = MagicMock()
        MockResearch.return_value = mock_research_inst
        MockPlan.return_value = mock_plan_inst

        def research_side_effect(task_id):
            from utils.task_manager import TaskManager
            tm = TaskManager(tasks_file)
            tm.update_status(task_id, "done")

        def plan_side_effect(task_id):
            from utils.task_manager import TaskManager
            tm = TaskManager(tasks_file)
            tm.update_status(task_id, "done")

        mock_research_inst.run.side_effect = research_side_effect
        mock_plan_inst.run.side_effect = plan_side_effect

        orch = Orchestrator(tasks_file=tasks_file, output_dir=output_dir)
        orch.run()

    mock_research_inst.run.assert_called_once_with("task_research")
    mock_plan_inst.run.assert_called_once_with("task_planning")


def test_orchestrator_retries_on_failure(tmp_env):
    tmp_path, tasks_file, output_dir = tmp_env
    init_pipeline_tasks(tasks_file, output_dir)

    call_count = {"n": 0}

    with patch("orchestrator.ResearchAgent") as MockResearch, \
         patch("orchestrator.PlanAgent"):

        mock_inst = MagicMock()
        MockResearch.return_value = mock_inst

        def fail_twice(task_id):
            from utils.task_manager import TaskManager
            tm = TaskManager(tasks_file)
            call_count["n"] += 1
            if call_count["n"] < 3:
                tm.update_status(task_id, "failed", error="timeout")
                raise RuntimeError("timeout")
            tm.update_status(task_id, "done")

        mock_inst.run.side_effect = fail_twice

        with patch("orchestrator.PlanAgent") as MockPlan:
            mock_plan = MagicMock()
            MockPlan.return_value = mock_plan
            mock_plan.run.side_effect = lambda tid: __import__(
                'utils.task_manager', fromlist=['TaskManager']
            ).TaskManager(tasks_file).update_status(tid, "done")

            orch = Orchestrator(tasks_file=tasks_file, output_dir=output_dir, max_retries=3)
            orch.run()

    assert call_count["n"] == 3


def test_orchestrator_halts_after_max_retries(tmp_env):
    tmp_path, tasks_file, output_dir = tmp_env
    init_pipeline_tasks(tasks_file, output_dir)

    with patch("orchestrator.ResearchAgent") as MockResearch:
        mock_inst = MagicMock()
        MockResearch.return_value = mock_inst

        def always_fail(task_id):
            from utils.task_manager import TaskManager
            tm = TaskManager(tasks_file)
            tm.update_status(task_id, "failed", error="always fails")
            raise RuntimeError("always fails")

        mock_inst.run.side_effect = always_fail

        orch = Orchestrator(tasks_file=tasks_file, output_dir=output_dir, max_retries=3)
        with pytest.raises(SystemExit):
            orch.run()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator'`

- [ ] **Step 3: Implement orchestrator.py**

Create `orchestrator.py`:

```python
import sys
import time
from pathlib import Path
from utils.task_manager import TaskManager
from utils.logger import get_logger
from agents.research_agent import ResearchAgent
from agents.plan_agent import PlanAgent

MAX_RETRIES = 3
POLL_INTERVAL = 1  # seconds


AGENT_MAP = {
    "research": ResearchAgent,
    "planning": PlanAgent,
}


def init_pipeline_tasks(tasks_file: Path, output_dir: Path):
    import json
    data = {
        "tasks": [
            {
                "id": "task_research",
                "type": "research",
                "status": "pending",
                "description": "Research market trends and choose best SaaS opportunity",
                "depends_on": [],
                "output_file": str(output_dir / "idea.md"),
                "retries": 0,
                "error": None
            },
            {
                "id": "task_planning",
                "type": "planning",
                "status": "pending",
                "description": "Generate architecture.md, stack.md, and tasks.json from idea.md",
                "depends_on": ["task_research"],
                "output_file": str(output_dir / "tasks.json"),
                "retries": 0,
                "error": None
            }
        ]
    }
    tasks_file.write_text(json.dumps(data, indent=2))


class Orchestrator:
    def __init__(self, tasks_file: Path, output_dir: Path, max_retries: int = MAX_RETRIES):
        self.tasks_file = Path(tasks_file)
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries
        self.tm = TaskManager(self.tasks_file)
        self.logger = get_logger("orchestrator")

    def _dispatch(self, task: dict):
        task_type = task["type"]
        task_id = task["id"]

        if task_type not in AGENT_MAP:
            self.logger.error(f"Unknown task type: {task_type}")
            self.tm.update_status(task_id, "blocked", error=f"no agent for type {task_type}")
            return

        AgentClass = AGENT_MAP[task_type]

        if task_type == "planning":
            agent = AgentClass(tasks_file=self.tasks_file, output_dir=self.output_dir)
        else:
            agent = AgentClass(tasks_file=self.tasks_file)

        retries = 0
        while retries < self.max_retries:
            try:
                self.logger.info(f"Dispatching {task_type} agent for {task_id} (attempt {retries + 1})")
                agent.run(task_id)
                return
            except Exception as e:
                retries += 1
                self.tm.increment_retries(task_id)
                self.logger.warning(f"Task {task_id} failed (attempt {retries}): {e}")
                if retries < self.max_retries:
                    self.tm.update_status(task_id, "pending")
                    time.sleep(POLL_INTERVAL)

        self.logger.error(f"Task {task_id} blocked after {self.max_retries} retries")
        self.tm.update_status(task_id, "blocked", error=f"exceeded max retries ({self.max_retries})")

    def run(self):
        self.logger.info("Orchestrator started")

        while not self.tm.all_done():
            if self.tm.any_blocked():
                self.logger.error("Pipeline halted — blocked task detected")
                sys.exit(1)

            task = self.tm.get_next_ready_task()
            if task is None:
                time.sleep(POLL_INTERVAL)
                continue

            self._dispatch(task)

        self.logger.info("Pipeline complete")


if __name__ == "__main__":
    tasks_file = Path("tasks.json")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    init_pipeline_tasks(tasks_file, output_dir)
    orch = Orchestrator(tasks_file=tasks_file, output_dir=output_dir)
    orch.run()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add orchestrator Phase 1 — research + planning pipeline"
```

---

## Task 8: Smoke test end-to-end

> This task runs the real pipeline against Gemini CLI. Requires `gemini` installed and authenticated.

**Files:** none (runtime only)

- [ ] **Step 1: Verify gemini CLI available**

```bash
gemini --version
```

Expected: prints version number. If not found, install with `npm install -g @google/gemini-cli`.

- [ ] **Step 2: Run the pipeline**

```bash
python orchestrator.py
```

Expected:
- `output/idea.md` created with market research content
- `output/architecture.md` created
- `output/stack.md` created
- `output/tasks.json` created with 8-15 tasks
- `logs/` directory contains 3 log files
- Terminal shows pipeline complete

- [ ] **Step 3: Inspect outputs**

```bash
cat output/idea.md
cat output/architecture.md
cat output/tasks.json | python -m json.tool
```

Expected: valid, substantive content in each file.

- [ ] **Step 4: Commit outputs as reference**

```bash
git add output/ logs/
git commit -m "chore: add Phase 1 smoke test outputs as reference"
```

---

## Summary

Phase 1 delivers a working research + planning pipeline:

| Component | Status after this plan |
|---|---|
| `utils/task_manager.py` | Complete + tested |
| `utils/logger.py` | Complete |
| `agents/base_agent.py` | Complete + tested |
| `agents/research_agent.py` | Complete + tested |
| `agents/plan_agent.py` | Complete + tested |
| `orchestrator.py` | Complete + tested |

**Phase 2** adds `code_agent.py` + `test_agent.py` consuming the `output/tasks.json` generated here.
