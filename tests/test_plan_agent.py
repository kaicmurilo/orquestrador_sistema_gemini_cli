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
