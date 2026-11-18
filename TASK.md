# TASK.md: Implementar cancelamento com reembolso automático

| Campo | Valor |
|---|---|
| ID | `TASK-F3-01` |
| Origem | [`SPEC.md §3.3 (SPEC-F3)`](SPEC.md#33-spec-f3-cancelamento-de-consulta-com-reembolso-automático) |
| Detalhamento | [`specs/cancelamento-reembolso.md`](specs/cancelamento-reembolso.md) (v1.2) |
| Executor | [`AGENT.md`](AGENT.md) (`AGENT-impl-cancelamento`) |
| Ferramentas permitidas | [`TOOLS.md`](TOOLS.md) |
| Status | Esboço. Liberada para execução quando o passo 0 for cumprido |

## Pré-requisitos

- [ ] Suíte atual passando: `python3 -m unittest discover -s backend/tests -t backend`.
- [ ] Os campos "Status" e "Aprovador" do cabeçalho de `specs/cancelamento-reembolso.md` mostram a aprovação do tech lead (etapa 3 do fluxo).

## Passos

Cada passo cita a seção da spec que ele cumpre. O conteúdo da regra está na spec e não é repetido aqui.

| # | Passo | Cumpre | Arquivos |
|---|---|---|---|
| 0 | **Checkpoint 1:** rodar `/revisar-spec specs/cancelamento-reembolso.md` e **parar** se o veredito for "PRECISA DE AJUSTES" | `docs/ex09-fluxo-spec-driven.md` | — |
| 1 | Criar `calcular_reembolso` e as constantes de prazo | `specs/cancelamento-reembolso.md §4` | `backend/agendamento/reembolso.py` |
| 2 | Adicionar `buscar_por_id` (aditivo), que entrega o F2-CA4, do qual o F3 depende | `SPEC.md §3.2` F2-CA4; `specs/…§6.3` | `backend/agendamento/pacientes.py` |
| 3 | Criar `EstadoConsulta`, `ResultadoCancelamento`, `Consulta` e `RepositorioConsultas` | `specs/cancelamento-reembolso.md §6.1` | `backend/agendamento/consultas.py` |
| 4 | Criar a porta `GatewayPagamento`, `ErroGateway` e `GatewayFake` | `specs/cancelamento-reembolso.md §6.1`, `§6.2` | `backend/agendamento/pagamento.py` |
| 5 | Adicionar os 3 templates, o parâmetro `extras` e a formatação de `valor` | `SPEC.md §3.4` F4-CA3, F4-CA4; `specs/…§6.3` | `backend/agendamento/notificacao.py` |
| 6 | Criar `ServicoCancelamento.cancelar`, com o fluxo de 8 passos, o lock por consulta e o logger | `specs/cancelamento-reembolso.md §3`, `§5` (B1–B8) | `backend/agendamento/cancelamento.py` |
| 7 | Escrever um teste por critério: F3-CA1 a F3-CA13, F2-CA4, F4-CA3 e F4-CA4 | `specs/cancelamento-reembolso.md §7`; `SPEC.md §3.2`, `§3.4` | `backend/tests/test_cancelamento.py` |
| 8 | Rodar a suíte completa e `python3 relatorios/relatorio_ocupacao.py` | F3-CA10 | — |
| 9 | **Checkpoint 2:** pedir a revisão do subagente `revisor-spec` com `SPEC.md §3.3` | `AGENT.md`, seção "Revisão obrigatória" | — |

## Definição de pronto

- [ ] Todos os critérios **F3-CA1 a F3-CA13**, **F2-CA4**, **F4-CA3** e **F4-CA4** com teste passando, e o nome de cada teste citando o critério.
- [ ] Os testes que já existiam continuam passando, sem nenhuma alteração neles.
- [ ] Nenhum arquivo alterado fora da coluna "Arquivos" acima.
- [ ] O relatório do `revisor-spec` não aponta "não atendido" nem "escopo extra".
- [ ] PR aberto com o relatório de saída abaixo e aprovado por um humano.

## Relatório de saída (o executor preenche no PR)

```markdown
## TASK-F3-01: relatório
- Critérios: F3-CA1 … F3-CA13, F2-CA4, F4-CA3, F4-CA4 → <teste correspondente> → OK/FALHA
- Arquivos alterados: <saída de git diff --stat>
- Pendências escaladas (AGENT.md, "Quando parar"): <nenhuma | descrição + seção da spec>
- Revisão revisor-spec: <veredito>
```
