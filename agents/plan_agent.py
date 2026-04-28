import json
from pathlib import Path
from agents.base_agent import call_gemini
from utils.task_manager import TaskManager
from utils.logger import get_logger

IDEA_CONSTRAINTS = """
Restrições globais (a ideia e o plano devem obedecer):
- Não projetar produto cujo core seja IA generativa, LLM, chatbot “inteligente” ou automação dependente de inferência paga por token.
- Arquitetura e stack devem ser economicamente sustentáveis: poucos serviços gerenciados caros, sem necessidade de GPUs ou filas de ML.
- Resolver problema real de usuários concretos; evitar “camada de IA” desnecessária.
- O produto atende o mercado brasileiro: hospedagem/compliance pensados para LGPD quando houver dados pessoais, integrações típicas do país (ex.: PIX, NFS-e, gateways/adquirentes locais) apenas se fizer sentido na ideia — não invente requisitos legais; descreva o que a ideia de fato exige.
- Documentos e UX assumem português do Brasil como padrão.
"""

ARCHITECTURE_PROMPT = IDEA_CONSTRAINTS + """
Com base na seguinte ideia de produto, gere um documento de arquitetura de software em markdown.

{idea}

Inclua:
- ## Visão Geral (2-3 frases)
- ## Componentes (liste cada serviço/módulo com descrição de uma linha)
- ## Fluxo de Dados (como os dados se movem entre os componentes)
- ## Decisões de Design (por que esta arquitetura é adequada para o produto)
"""

STACK_PROMPT = IDEA_CONSTRAINTS + """
Com base na seguinte ideia de produto e arquitetura, recomende um stack tecnológico em markdown.

{idea}

{architecture}

Inclua:
- ## Backend
- ## Frontend
- ## Banco de Dados
- ## Infraestrutura
- ## Por Que Este Stack (justificativa breve por escolha)
"""

TASKS_PROMPT = IDEA_CONSTRAINTS + """
Com base na seguinte ideia de produto, arquitetura e stack, gere uma lista de tarefas JSON para agentes de codificação autônomos.

{idea}

{architecture}

{stack}

Retorne APENAS JSON válido (sem markdown, sem explicação) com este schema exato:
{{
  "tasks": [
    {{
      "id": "task_001",
      "type": "code",
      "status": "pending",
      "description": "descrição do que construir",
      "depends_on": [],
      "output_file": "workspace/caminho/para/arquivo.py",
      "retries": 0,
      "error": null
    }}
  ]
}}

Regras:
- Divida em tarefas pequenas, de arquivo único
- Defina depends_on com os ids das tarefas que devem ser concluídas primeiro
- output_file deve ser um caminho dentro de workspace/
- Gere 8-15 tarefas cobrindo o MVP completo
- Nenhuma tarefa pode ser integração com OpenAI, Anthropic, Gemini API, embeddings, RAG, fine-tuning ou feature “AI” genérica
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
            if "tasks" not in tasks_data:
                raise ValueError(f"Gemini tasks JSON missing 'tasks' key: {str(tasks_data)[:200]}")
            tasks_out = self.output_dir / "tasks.json"
            tasks_out.write_text(json.dumps(tasks_data, indent=2))
            self.logger.info(f"tasks.json written with {len(tasks_data['tasks'])} tasks")

            self.tm.update_status(task_id, "done")

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            self.tm.update_status(task_id, "failed", error=str(e))
            raise
