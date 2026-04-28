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
