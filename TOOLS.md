# TOOLS.md: Ferramentas e módulos acessíveis

| Campo | Valor |
|---|---|
| Vale para | [`TASK.md`](TASK.md) (`TASK-F3-01`), executada por [`AGENT.md`](AGENT.md) |
| Escopo derivado de | [`SPEC.md §3.3`](SPEC.md#33-spec-f3-cancelamento-de-consulta-com-reembolso-automático), seção "Código afetado", e [`specs/cancelamento-reembolso.md §6`](specs/cancelamento-reembolso.md) |
| Aplicação técnica | `.claude/settings.json` (`allow` / `ask` / `deny`) e `--allowedTools` na execução headless. A coluna **Aplicação** de cada tabela diz se a regra é **imposta** pela ferramenta ou se é só **convenção** (o agente cumpre e o revisor confere) |

## 1. Ferramentas do Claude Code

| Ferramenta | Permissão | Aplicação | Observação |
|---|---|---|---|
| `Read`, `Grep`, `Glob` | Liberada | Imposta | `.env*` está bloqueado em `deny` para `Read`, `Grep` e `Edit` |
| `Edit` / `Write` em `backend/agendamento/**` e `backend/tests/**` | Liberada (`allow`) | Imposta (pasta) e convenção (arquivo) | As exceções abaixo pedem confirmação. Dentro do que sobra, o agente só edita os arquivos da coluna "Arquivos" do `TASK.md` |
| `Edit` em `disponibilidade.py`, `validacao_config.py`, `test_modulos.py`, `test_validacao_config.py` | Pede confirmação (`ask`) | Imposta | São os módulos e testes existentes que a tarefa não pode alterar (`AGENT.md`, seção "Limites") |
| `Edit` em `config/**`, `SPEC.md`, `specs/**`, `AGENT.md`, `TASK.md`, `TOOLS.md`, `.claude/**` | Pede confirmação (`ask`) | Imposta | O agente deve escalar em vez de pedir |
| `Bash(python3 -m unittest *)` | Liberada (`allow`) | Imposta | Suíte completa ou testes isolados |
| `Bash(python3 relatorios/relatorio_ocupacao.py*)` | Liberada (`allow`) | Imposta | Não altera a agenda, só grava o CSV em `relatorios/saida/` (ignorado pelo git) |
| `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)` | Liberada (`allow`) | Imposta | Para montar o relatório de saída |
| `Bash(git commit*)`, `Bash(python3 scripts/migracao/*)` | Pede confirmação (`ask`) | Imposta | A migração não é necessária nesta tarefa |
| `Bash(* --aplicar*)`, `Bash(git push*)`, `WebFetch`, `WebSearch` | **Bloqueada** (`deny`) | Imposta | A tarefa não depende de nada externo |
| Skill `/revisar-spec` | Liberada, **obrigatória** no passo 0 | Convenção | Checkpoint 1 |
| Subagente `revisor-spec` | Liberado, **obrigatório** no passo 9 | Convenção | Checkpoint 2. O subagente só tem `Read`, `Grep`, `Glob` e `Bash` (definido em `.claude/agents/revisor-spec.md`) |

## 2. Módulos do projeto

| Módulo | Acesso | O que pode usar ou mudar | Referência na spec |
|---|---|---|---|
| `backend/agendamento/disponibilidade.py` | **Só leitura e chamada** | Chamar `AgendaDisponibilidade.reservar`, `liberar`, `slots_do_dia` | `SPEC.md §3.1`, `§3.3` |
| `backend/agendamento/pacientes.py` | **Leitura + adição** | Adicionar `buscar_por_id` e o índice `_por_id`. Não mudar os métodos que já existem | `SPEC.md §3.2` F2-CA4 |
| `backend/agendamento/notificacao.py` | **Leitura + adição** | Adicionar 3 entradas em `TEMPLATES` e o parâmetro opcional `extras` em `notificar` | `SPEC.md §3.4` |
| `backend/agendamento/validacao_config.py` | Não usar | Fora de escopo | `SPEC.md §3.1` |
| `backend/agendamento/{consultas,pagamento,reembolso,cancelamento}.py` | **Criação** | Arquivos novos desta tarefa | `specs/cancelamento-reembolso.md §6.1` |
| `backend/tests/test_cancelamento.py` | **Criação** | Testes novos | `specs/cancelamento-reembolso.md §7` |
| `backend/tests/test_modulos.py`, `test_validacao_config.py` | **Só leitura** | Executar, não alterar | `AGENT.md`, seção "Limites" |
| `config/horarios-*.json` | **Só leitura** | — | `CLAUDE.md`, seção "Proibido sem aprovação" |
| `scripts/migracao/`, `relatorios/` | **Só leitura** | Rodar o relatório para o F3-CA10 | `SPEC.md §3.3` F3-CA10 |
| `SPEC.md`, `specs/`, `AGENT.md`, `TASK.md`, `TOOLS.md` | **Só leitura** | Mudanças passam pelo tech lead | `SPEC.md §5` R1 |

## 3. Dublês de teste disponíveis

| Dublê | Onde | Para quê |
|---|---|---|
| `CanalConsole` | `notificacao.py` (já existe) | Conferir as mensagens enviadas e simular falha do canal (B6) com uma subclasse no teste |
| `GatewayFake` | `pagamento.py` (passo 4) | Registrar estornos e simular falha (`falhar_proximas`), timeout depois do estorno (`estornar_e_falhar_proxima`) e concorrência (`ao_reembolsar`) |
| Relógio injetado | parâmetro `relogio` de `ServicoCancelamento` | Datas fixas de nov/2026 (`backend/CLAUDE.md`) |
| `assertLogs` | `unittest` | Conferir o log sem dados pessoais (CA9) |
