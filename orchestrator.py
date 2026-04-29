import sys
import json
import time
from pathlib import Path
from utils.task_manager import TaskManager
from utils.logger import get_logger
from agents.research_agent import ResearchAgent
from agents.plan_agent import PlanAgent
from agents.product_agent import ProductAgent

MAX_RETRIES = 3
POLL_INTERVAL = 1  # seconds


AGENT_MAP = {
    "research": ResearchAgent,
    "planning": PlanAgent,
    "product": ProductAgent,
}


PIPELINE_TASKS = [
    {
        "id": "task_research",
        "type": "research",
        "status": "pending",
        "description": "Pesquisar oportunidades no Brasil (mercado local) e escolher ideia barata de operar, sem IA como produto",
        "depends_on": [],
        "retries": 0,
        "error": None,
    },
    {
        "id": "task_planning",
        "type": "planning",
        "status": "pending",
        "description": "Generate architecture.md, stack.md, and tasks.json from idea.md",
        "depends_on": ["task_research"],
        "retries": 0,
        "error": None,
    },
    {
        "id": "task_product",
        "type": "product",
        "status": "pending",
        "description": "Enriquecer tasks.json com critérios de aceite, prioridade e dependências (PM + PO)",
        "depends_on": ["task_planning"],
        "retries": 0,
        "error": None,
    },
]


def init_pipeline_tasks(tasks_file: Path, output_dir: Path):
    """Initialize tasks.json if missing, or merge new pipeline tasks without resetting done ones."""
    # Build canonical tasks with output_file resolved
    canonical = []
    output_file_map = {
        "task_research": str(output_dir / "idea.md"),
        "task_planning": str(output_dir / "tasks.json"),
        "task_product": str(output_dir / "tasks.json"),
    }
    for t in PIPELINE_TASKS:
        entry = dict(t)
        entry["output_file"] = output_file_map.get(t["id"], "")
        canonical.append(entry)

    if not tasks_file.exists():
        tasks_file.write_text(json.dumps({"tasks": canonical}, indent=2))
        return

    # File exists — merge: preserve existing tasks, append missing ones
    existing = json.loads(tasks_file.read_text())
    existing_tasks = existing.get("tasks", [])
    existing_ids = {t["id"] for t in existing_tasks}

    for entry in canonical:
        if entry["id"] not in existing_ids:
            existing_tasks.append(entry)

    tasks_file.write_text(json.dumps({"tasks": existing_tasks}, indent=2))


class Orchestrator:
    def __init__(self, tasks_file: Path, output_dir: Path, max_retries: int = MAX_RETRIES, poll_interval: int = POLL_INTERVAL):
        self.tasks_file = Path(tasks_file)
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.tm = TaskManager(self.tasks_file)
        self.logger = get_logger("orchestrator")

    def _dispatch(self, task: dict):
        task_type = task["type"]
        task_id = task["id"]

        if task_type not in AGENT_MAP:
            self.logger.error(f"Unknown task type: {task_type}")
            self.tm.update_status(task_id, "blocked", error=f"no agent for type {task_type}")
            return

        AgentClass = getattr(sys.modules[__name__], AGENT_MAP[task_type].__name__)

        retries = 0
        while retries < self.max_retries:
            try:
                if task_type in ("planning", "product"):
                    agent = AgentClass(tasks_file=self.tasks_file, output_dir=self.output_dir)
                else:
                    agent = AgentClass(tasks_file=self.tasks_file)
                self.logger.info(f"Dispatching {task_type} agent for {task_id} (attempt {retries + 1})")
                agent.run(task_id)
                return
            except Exception as e:
                retries += 1
                self.tm.increment_retries(task_id)
                self.logger.warning(f"Task {task_id} failed (attempt {retries}): {e}")
                if retries < self.max_retries:
                    self.tm.update_status(task_id, "pending")
                    time.sleep(self.poll_interval)

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
                time.sleep(self.poll_interval)
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
