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
