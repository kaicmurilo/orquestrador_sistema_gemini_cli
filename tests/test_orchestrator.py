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
