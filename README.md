# Agentes Autônomos

Pipeline de agentes Python autônomos que usam o **Gemini CLI** para pesquisar ideias de mercado, planejar e construir sistemas completos do zero — cobrindo todos os papéis de uma empresa de software.

## Como Funciona

Fluxo alvo (✓ = já existe no código; ○ = a implementar). A ordem privilegia **contexto → design → código → revisão → medição → correção → segurança → release → governança**.

```
python3 orchestrator.py
  ✓ Coordenação      — orchestrator + TaskManager (fila, retries, dependências)
  ✓ research_agent   — oportunidade de mercado (web search) → output/idea.md
  ✓ plan_agent       — arquitetura, stack, backlog inicial → output/
  ○ product_agent    — PM + PO: refinar tasks.json, critérios de aceite, prioridade
  ○ tech_lead_agent  — CTO: ADRs, aderência idea.md ↔ architecture.md ↔ workspace/
  ○ ux_agent         — Designer: wireframes, fluxos, decisões de UI → output/ux/
  ○ code_agent       — implementação tarefa a tarefa → workspace/
  ○ test_agent       — smoke tests por entrega → workspace/tests/
  ○ review_agent     — revisão de diff/PR antes de merge, abre tasks "review_fix"
  ○ qa_agent         — ampliar testes, pytest → tasks "fix" com contexto
  ○ bug_agent        — varredura lógica/edge cases → tasks "fix"
  ○ security_agent   — AppSec → output/security_report.md + tasks "security_fix"
  ○ fix_agent        — loop: consome "fix" / "review_fix" / "security_fix", valida, marca done
  ○ docs_agent       — API docs, guia de usuário, changelog → output/docs/
  ○ infra_agent      — CI/CD, container, ambientes, política de secrets
  ○ monitor_agent    — SLOs, alertas, dashboards pós-deploy → output/monitoring/
  ○ feedback_agent   — simula usuário real, abre tasks de melhoria
  ○ pmo_agent        — gates entre fases, métricas, critérios de parada, orçamento
```

**Papéis (personas) e quem cobre no pipeline**

| Persona | Foco | No repo (hoje / previsto) |
|--------|------|----------------------------|
| **Coordinator** | Orquestração da fila, estado, retries | `orchestrator.py`, `utils/task_manager.py` |
| **PO** (Product Owner) | Problema, valor, escopo MVP, "o quê" entregar | hoje no `research_agent`; refinamento via `product_agent` |
| **PM** (Product Manager) | Backlog priorizado, dependências, critérios de aceite | hoje parcial no `plan_agent`; dedicado no `product_agent` |
| **CTO / Arquiteto** | Stack, ADRs, consistência arquitetural | `plan_agent` (docs em `output/`); drift pós-código via `tech_lead_agent` |
| **Designer / UX** | Wireframes, fluxos, decisões de interface | futuro `ux_agent` → `output/ux/` |
| **Eng** (Engenheiro) | Implementação, patches, correções | futuro `code_agent` + `fix_agent` |
| **Tech Lead / Reviewer** | Revisão de código, qualidade antes de merge | futuro `review_agent` |
| **QA** | Testes, evidência de regressão | futuro `test_agent` + `qa_agent` + `bug_agent` |
| **AppSec** | Segurança, CVEs, superfície de ataque | futuro `security_agent` |
| **Tech Writer** | Documentação técnica, changelog, guia de usuário | futuro `docs_agent` |
| **Infra / DevOps** | Pipeline de build, imagem, secrets, ambientes | futuro `infra_agent` |
| **SRE / Monitor** | SLOs, alertas, observabilidade pós-deploy | futuro `monitor_agent` |
| **CO** (operação de entrega) | "Done" ponta a ponta, handoff entre agentes | documentado aqui; pode fundir com Coordinator + PMO na v1 |
| **PMO** | Gates entre fases, risco, ritmo, critério de parada | futuro `pmo_agent` ou regras no orchestrator |

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

### Fase 0 — Coordenação (ativo)

**Personas:** Coordinator (+ CO/PMO na visão de produto: uma fila, um estado, critérios de "done" por task).

O `orchestrator.py` despacha tasks conforme `depends_on`, aplica retries e persiste estado em `tasks.json` via `TaskManager`. Evolução natural: políticas de orçamento (tempo máximo, limite de chamadas ao Gemini) e **gates** entre blocos de fase (responsabilidade do `pmo_agent`).

### Fase 1 — Oportunidade de mercado (implementado)

```bash
python3 orchestrator.py
```

1. Pesquisar tendências / oportunidade via Gemini CLI (web search).
2. Consolidar escolha em `output/idea.md` (**PO**: problema e valor).

Logs em `logs/` — um arquivo por agente por execução.

### Fase 2 — Produto, arquitetura e backlog (implementado)

O `plan_agent` gera documentação técnica e backlog inicial. Arquivos em `output/`:

```
output/
├── idea.md           # oportunidade / visão (PO)
├── architecture.md   # arquitetura (CTO)
├── stack.md          # stack (CTO)
└── tasks.json        # backlog para implementação (PM; consumido pelo Coordinator)
```

### Fase 3 — Refinamento de produto (a implementar)

**Personas:** PM + PO.

- **`product_agent`** — enriquece `output/tasks.json` com critérios de aceite, prioridade e dependências explícitas; garante alinhamento com `idea.md`.

### Fase 4 — Liderança técnica (a implementar)

**Persona:** CTO / Arquiteto.

- **`tech_lead_agent`** — valida ADRs, detecta **drift** entre `architecture.md` / `stack.md` e `workspace/`, abre tasks de alinhamento quando necessário.

### Fase 5 — UX e design (a implementar)

**Persona:** Designer / UX.

- **`ux_agent`** — produz wireframes, fluxos de usuário e decisões de interface em `output/ux/` antes do `code_agent` iniciar, evitando retrabalho de layout/navegação.

### Fase 6 — Implementação (a implementar)

**Personas:** Eng + Tech Lead.

- **`code_agent`** — executa tasks de implementação em `workspace/` (criar/editar arquivos conforme `tasks.json`).
- **`test_agent`** — após cada entrega relevante, roda testes mínimos / smoke no que foi gerado em `workspace/tests/`.

Sem esta fase, não há alvo estável para revisão, QA, bug hunt, segurança ou infra.

### Fase 7 — Revisão de código (a implementar)

**Persona:** Tech Lead / Reviewer.

- **`review_agent`** — inspeciona diff/PR gerado pelo `code_agent`, verifica aderência a `architecture.md` e boas práticas, cria tasks `"review_fix"` antes de qualquer merge.

Revisão separada de QA: **review_agent** olha o código; **qa_agent** olha o comportamento.

### Fase 8 — Qualidade e regressão (a implementar)

**Persona:** QA.

- **`qa_agent`** — amplia testes (unitário/integração), roda `pytest` no `workspace/`, parseia falhas e cria tasks `"fix"` com stack trace / contexto.

Ordem intencional: **testes e evidência de regressão antes** de varreduras amplas de bug, para o `fix_agent` ter sinal claro.

### Fase 9 — Estabilização e bugs (a implementar)

**Personas:** QA + Eng.

- **`bug_agent`** — varre `workspace/` (lógica, edge cases, tipagem, inconsistência entre módulos), abre tasks `"fix"`. Um único executor de correção (`fix_agent`) evita conflito de múltiplos "donos" do mesmo arquivo.

### Fase 10 — Segurança (a implementar)

**Persona:** AppSec.

- **`security_agent`** — XSS, injeção, secrets hardcoded, auth em endpoints, CVEs em dependências → `output/security_report.md` + tasks `"security_fix"` por severidade.

### Fase 11 — Correção contínua (a implementar)

**Personas:** Eng (+ Coordinator na fila).

- **`fix_agent`** — loop: próxima task `"fix"`, `"review_fix"` ou `"security_fix"`, patch via Gemini CLI no alvo em `workspace/`, revalidação (testes quando existirem), marca `done` até fila esgotada ou limite PMO/orçamento.

### Fase 12 — Documentação (a implementar)

**Persona:** Tech Writer.

- **`docs_agent`** — gera API docs, guia de usuário, changelog e README do projeto em `output/docs/` com base no código estável em `workspace/`.

Documentação gerada após estabilização (fases de fix concluídas) garante que reflete o estado real do produto.

### Fase 13 — Infra, release e operação (a implementar)

**Personas:** Infra/DevOps + CO.

- **`infra_agent`** — CI mínimo, Dockerfile ou equivalente, política de secrets, ambientes (dev/stage), checklist de release.
- **CO** — "done" de release: artefato versionado, pipeline verde, critérios acordados com PMO.

### Fase 14 — Monitoramento (a implementar)

**Persona:** SRE / Monitor.

- **`monitor_agent`** — define SLOs, configura alertas e dashboards pós-deploy em `output/monitoring/`; gera tasks de melhoria quando SLOs são violados.

### Fase 15 — Feedback e melhoria contínua (a implementar)

**Persona:** CO + PO.

- **`feedback_agent`** — simula usuário real, exercita fluxos do produto, abre tasks de melhoria e fecha o loop com o `product_agent` para próxima iteração.

### Transversal — PMO e autonomia segura

Incluir cedo no desenho (mesmo antes de todos os agentes):

- **Critérios de parada:** fila vazia, teto de iterações, ou "zero findings críticos" em segurança, conforme produto.
- **Sandbox:** o que o Gemini CLI pode executar (rede, shell, escrita fora de `workspace/`).
- **Observabilidade:** correlacionar `task_id` → agente → artefatos (além dos logs por arquivo).

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
│   ├── research_agent.py    # pesquisa de mercado (Fase 1)
│   ├── plan_agent.py        # geração de arquitetura e tarefas (Fase 2)
│   ├── product_agent.py     # refinamento de produto — a implementar (Fase 3)
│   ├── tech_lead_agent.py   # liderança técnica / drift — a implementar (Fase 4)
│   ├── ux_agent.py          # wireframes e fluxos de UX — a implementar (Fase 5)
│   ├── code_agent.py        # implementação — a implementar (Fase 6)
│   ├── test_agent.py        # smoke tests por entrega — a implementar (Fase 6)
│   ├── review_agent.py      # revisão de código — a implementar (Fase 7)
│   ├── qa_agent.py          # qualidade e regressão — a implementar (Fase 8)
│   ├── bug_agent.py         # varredura de bugs — a implementar (Fase 9)
│   ├── security_agent.py    # segurança (AppSec) — a implementar (Fase 10)
│   ├── fix_agent.py         # correção contínua — a implementar (Fase 11)
│   ├── docs_agent.py        # documentação técnica — a implementar (Fase 12)
│   ├── infra_agent.py       # CI/CD e infra — a implementar (Fase 13)
│   ├── monitor_agent.py     # monitoramento e SLOs — a implementar (Fase 14)
│   └── feedback_agent.py    # feedback e melhoria contínua — a implementar (Fase 15)
├── utils/
│   ├── task_manager.py      # estado do pipeline (tasks.json)
│   └── logger.py            # logs por agente
├── output/                  # arquivos gerados pelo pipeline
│   ├── idea.md
│   ├── architecture.md
│   ├── stack.md
│   ├── tasks.json
│   ├── security_report.md   # gerado pelo security_agent
│   ├── ux/                  # wireframes e fluxos (ux_agent)
│   ├── docs/                # documentação técnica (docs_agent)
│   └── monitoring/          # SLOs e alertas (monitor_agent)
├── workspace/               # projeto gerado pelos agentes (code_agent)
├── logs/                    # logs de execução
└── tests/                   # testes unitários do pipeline
```

## Variáveis de Ambiente

Nenhuma. Autenticação é feita via Gemini CLI (`gemini auth`).

## Recomeçar do Zero

Para limpar os outputs e rodar novamente:

```bash
rm -f output/*.md output/*.json
python3 orchestrator.py
```
