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
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task is None:
            raise KeyError(f"task_id '{task_id}' not found")
        output_file = Path(task["output_file"])

        self.tm.update_status(task_id, "in_progress")
        self.logger.info(f"Starting research for task {task_id}")

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            result = call_gemini(RESEARCH_PROMPT)
            output_file.write_text(result)
            self.logger.info(f"idea.md written to {output_file}")
            self.tm.update_status(task_id, "done")
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            self.tm.update_status(task_id, "failed", error=str(e))
            raise
