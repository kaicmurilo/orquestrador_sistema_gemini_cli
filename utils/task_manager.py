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
