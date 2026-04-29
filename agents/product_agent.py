import json
from pathlib import Path
from agents.base_agent import call_gemini
from utils.task_manager import TaskManager
from utils.logger import get_logger

ENRICH_PROMPT = """
Você é PM + PO sênior. Receberá os documentos do produto e o backlog inicial.
Sua missão: enriquecer cada task do backlog com critérios de aceite, prioridade e dependências explícitas,
garantindo alinhamento com a ideia e arquitetura.

=== idea.md ===
{idea}

=== architecture.md ===
{architecture}

=== stack.md ===
{stack}

=== tasks.json (backlog inicial) ===
{tasks}

Retorne APENAS JSON válido (sem markdown, sem explicação) com o schema abaixo.
Preserve todos os campos originais de cada task. Adicione/sobrescreva apenas:
- "acceptance_criteria": lista de strings (condições observáveis que provam a task concluída)
- "priority": "high" | "medium" | "low"
- "depends_on": lista de task ids (pode reordenar ou complementar o original)
- "notes": string curta com contexto de PM/PO (opcional, pode ser "")

Regras:
- Não remova tasks; não adicione tasks novas.
- Critérios de aceite devem ser testáveis e específicos (evite "funcionar corretamente").
- Prioridades devem refletir MVP: o que bloqueia valor para o usuário vem primeiro (high).
- Retorne o JSON completo com a chave "tasks" contendo a lista enriquecida.
"""


def _extract_json(text: str) -> dict:
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char == '{':
            try:
                obj, _ = decoder.raw_decode(text, i)
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError(f"No valid JSON object found in output: {text[:200]}")


class ProductAgent:
    def __init__(self, tasks_file: Path, output_dir: Path = Path("output")):
        self.tm = TaskManager(Path(tasks_file))
        self.output_dir = Path(output_dir)
        self.logger = get_logger("product_agent")

    def run(self, task_id: str):
        self.tm.update_status(task_id, "in_progress")
        self.logger.info(f"Starting product refinement for task {task_id}")

        try:
            idea = (self.output_dir / "idea.md").read_text()
            architecture = (self.output_dir / "architecture.md").read_text()
            stack = (self.output_dir / "stack.md").read_text()
            tasks_path = self.output_dir / "tasks.json"
            tasks_raw = tasks_path.read_text()

            prompt = ENRICH_PROMPT.format(
                idea=idea,
                architecture=architecture,
                stack=stack,
                tasks=tasks_raw,
            )

            self.logger.info("Calling Gemini to enrich tasks.json")
            enriched_raw = call_gemini(prompt)
            enriched_data = _extract_json(enriched_raw)

            if "tasks" not in enriched_data:
                raise ValueError(f"Gemini response missing 'tasks' key: {str(enriched_data)[:200]}")

            tasks_path.write_text(json.dumps(enriched_data, indent=2))
            self.logger.info(f"tasks.json enriched with {len(enriched_data['tasks'])} tasks")

            self.tm.update_status(task_id, "done")

        except Exception as e:
            self.logger.error(f"Product refinement failed: {e}")
            self.tm.update_status(task_id, "failed", error=str(e))
            raise
