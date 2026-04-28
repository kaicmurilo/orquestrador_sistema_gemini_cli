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
