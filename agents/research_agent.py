from pathlib import Path
from agents.base_agent import call_gemini
from utils.task_manager import TaskManager
from utils.logger import get_logger

RESEARCH_PROMPT = """
Você é um analista de pesquisa de mercado focado no Brasil. Use busca na web priorizando fontes, reguladores, concorrentes e dores do mercado brasileiro (não assuma EUA/Europa como padrão).

Escopo geográfico e cultural:
- Todas as 5 oportunidades e a ideia escolhida devem ser viáveis e desejáveis para operar no Brasil (clientes, cobrança em BRL, conformidade local).
- Público-alvo, canais de venda e exemplos devem ser brasileiros (PME, MEI, cooperativas, setores típicos do país, cidades/estados quando fizer sentido).
- Cite onde aplicável: LGPD, obrigações fiscais/trabalhistas comuns no Brasil, NFS-e/nota fiscal, PIX, boletos, bancos/adquirentes usados no país — apenas o que for relevante à ideia, sem inventar norma.
- Timing “Por Que Agora” deve incluir gatilhos do contexto nacional (lei, hábito de consumo, infraestrutura local), não só tendência global genérica.

Restrições obrigatórias (não negociáveis):
- A ideia escolhida NÃO pode ter como núcleo APIs de LLM, chatbots genéricos, copilots, “AI assistants”, geração de texto/imagem/vídeo por modelo, nem qualquer monetização que dependa de tokens ou inferência paga como motor do produto.
- Não sugira “plataforma de IA”, “automação com GPT”, RAG como produto, nem ferramentas cujo valor principal seja “inteligência artificial”.
- Priorize produtos baratos de manter: lógica de negócio clara, poucos serviços pagos, infra previsível (ex.: app web + banco + filas simples ou até sem filas), evitando custo variável alto por usuário.
- O problema deve ser real e específico (ex.: conformidade chata, agendamento, estoque, cobrança, contratos, field service, nicho B2B pequeno), não hype de tecnologia.

Pesquise o seguinte:
1. Liste 5 oportunidades de software (podem ser SaaS ou produto digital) com demanda sustentável no Brasil e concorrência gerenciável em 2024-2026, respeitando as restrições acima.
2. Para cada uma: problema mensurável no contexto brasileiro, público-alvo no país, como cobrar de forma simples (BRL, modelo de preço comum aqui), concorrentes nacionais ou ativos forte no Brasil (se houver).
3. Escolha a melhor oportunidade e justifique com evidência ligada ao Brasil (dados, regulação, comportamento de mercado local; não opinião vaga).

Gere um documento markdown com:
- # Ideia Escolhida: [Nome]
- ## Contexto Brasil (1 parágrafo: por que esta ideia faz sentido aqui agora)
- ## Problema
- ## Mercado-Alvo
- ## Por Que Agora (timing de mercado no Brasil)
- ## Modelo de Monetização
- ## Panorama Competitivo
- ## Funcionalidades Principais (MVP, 5-7 itens; nenhuma dependente de modelo de linguagem ou APIs de IA generativa)
- ## Stack Tecnológico Recomendado (maduro, econômico de operar no Brasil; cite custo/previsibilidade em uma frase)
- ## Custo Operacional (estimativa qualitativa: baixo/médio e por quê)
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
