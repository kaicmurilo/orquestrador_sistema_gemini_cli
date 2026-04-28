# Agentes Autônomos

Pipeline de agentes Python autônomos que usam o **Gemini CLI** para pesquisar ideias de mercado, planejar e construir sistemas completos do zero.

## Como Funciona

```
python3 orchestrator.py
  → research_agent   — busca tendências via Gemini (web search) → output/idea.md
  → plan_agent       — gera arquitetura, stack e lista de tarefas → output/
  → [Phase 2] code_agent  — constrói o sistema tarefa a tarefa → workspace/
  → [Phase 2] test_agent  — valida o código gerado
```

## Pré-requisitos

- Python 3.11+
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) instalado e autenticado

```bash
# verificar instalação
gemini --version

# autenticar (primeira vez)
gemini auth
```

## Instalação

```bash
git clone <repo>
cd agentesAutonomos
pip install -r requirements.txt
```

## Rodando

### Phase 1 — Pesquisa + Planejamento

```bash
python3 orchestrator.py
```

O pipeline vai:
1. Pesquisar tendências de mercado via Gemini CLI (web search)
2. Escolher a melhor oportunidade de SaaS
3. Gerar arquitetura, stack e lista de tarefas

Arquivos gerados em `output/`:
```
output/
├── idea.md          # ideia escolhida com análise de mercado
├── architecture.md  # arquitetura do sistema
├── stack.md         # stack tecnológico recomendado
└── tasks.json       # tarefas para os agentes executores (Phase 2)
```

Logs em `logs/` — um arquivo por agente por execução.

### Rodar testes

```bash
pytest -v
```

## Estrutura do Projeto

```
agentesAutonomos/
├── orchestrator.py          # ponto de entrada — coordena o pipeline
├── agents/
│   ├── base_agent.py        # wrapper do Gemini CLI
│   ├── research_agent.py    # pesquisa de mercado
│   └── plan_agent.py        # geração de arquitetura e tarefas
├── utils/
│   ├── task_manager.py      # estado do pipeline (tasks.json)
│   └── logger.py            # logs por agente
├── output/                  # arquivos gerados pelo pipeline
├── workspace/               # projeto construído pelos agentes (Phase 2)
├── logs/                    # logs de execução
└── tests/                   # testes unitários
```

## Variáveis de Ambiente

Nenhuma. Autenticação é feita via Gemini CLI (`gemini auth`).

## Recomeçar do Zero

Para limpar os outputs e rodar novamente:

```bash
rm -f output/*.md output/*.json
python3 orchestrator.py
```
