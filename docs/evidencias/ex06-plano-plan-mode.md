# Plano: Cancelamento de consulta com reembolso automático

## Contexto

O serviço permite reservar (`AgendaDisponibilidade.reservar`) e liberar (`liberar`) slots, cadastrar
pacientes e notificar, mas **não existe o conceito de "consulta"**: `reservados` é só
`set[(medico_id, datetime)]`, sem ligação com paciente, valor pago ou estado. Sem isso não dá para
saber quem cancelou, quanto foi pago, se já foi cancelada ou se já foi realizada.
Também não há gateway de pagamento. O plano introduz o mínimo necessário (entidade `Consulta`,
porta `GatewayPagamento`, cálculo de reembolso, serviço de cancelamento) **sem alterar a interface
pública existente**, que `scripts/migracao/` e `relatorios/` consomem. Mudanças em `pacientes.py`
e `notificacao.py` são só aditivas.

Estado do repositório: `specs/`, `SPEC.md`, `TASK.md`, `AGENT.md` e `TOOLS.md` **não existem**
(o `CLAUDE.local.md` cita `specs/cancelamento-reembolso.md`, que ainda precisa ser criado).
Pelo fluxo da squad, o primeiro passo após aprovação é escrever essa spec a partir deste plano.

## Comportamento esperado

`ServicoCancelamento.cancelar(consulta_id)`:
1. Localiza a consulta (inexistente → `KeyError`).
2. Rejeita se já cancelada ou já realizada (`ValueError`).
3. Calcula o reembolso pela antecedência (`inicio - agora`).
4. Se reembolso > 0, chama o gateway. Falha no gateway → nada muda (consulta continua `AGENDADA`, slot continua reservado) e o erro sobe como `ErroGateway`.
5. Marca a consulta como `CANCELADA`, registrando instante, percentual e valor reembolsado.
6. Libera o slot via `agenda.liberar(medico_id, inicio)`.
7. Notifica o paciente (melhor esforço: falha de canal não desfaz o cancelamento).
8. Retorna um `ResultadoCancelamento` (consulta, percentual, valor reembolsado, referência do estorno).

Tempo injetado (`relogio: Callable[[], datetime]`, padrão `datetime.now`) para os testes não
dependerem de `date.today()` (regra do `backend/CLAUDE.md`). Datetimes são *naive* locais, como no
restante do código.

## Regras de prazo (proposta do usuário)

| Antecedência (`inicio - agora`) | Reembolso |
|---|---|
| `>= 24h` | 100% |
| `>= 2h` e `< 24h` | 50% |
| `< 2h` | 0% (cancela e libera o slot, sem reembolso) |

- Limites: exatamente 24h → 100%; exatamente 2h → 50% (intervalos fechados à esquerda).
- Valores em **centavos inteiros**; 50% arredonda para baixo (`valor * 50 // 100`).
- Constantes em um só lugar (`reembolso.py`) para facilitar ajuste.

## Condições de borda

| Caso | Comportamento |
|---|---|
| Fora do prazo (< 2h) | Cancelamento permitido, reembolso 0, gateway **não** é chamado, slot liberado, notificação "sem reembolso". |
| Cancelamento duplicado | `ValueError("Consulta já cancelada")`; não chama o gateway de novo nem notifica de novo (sem segundo reembolso). |
| Consulta inexistente | `KeyError("Consulta não encontrada")`. |
| Consulta já realizada (`inicio <= agora` ou estado `REALIZADA`) | `ValueError("Consulta já realizada")`; sem reembolso, slot intocado. |
| Falha no gateway | `ErroGateway`; estado inalterado e seguro para repetir. Chave de idempotência = id da consulta, para que um retry após timeout não estorne duas vezes. |
| Falha no canal de notificação | Cancelamento e reembolso permanecem; erro é registrado, não propagado. |
| Consulta sem pagamento (`valor_centavos == 0` ou sem `pagamento_ref`) | Reembolso 0, gateway não chamado. |

## Pontos de integração

- **`disponibilidade.py`**: `liberar(medico_id, inicio)` já existe e é idempotente (`discard`); é chamado só **depois** do reembolso bem-sucedido. Nenhuma mudança necessária. Efeito colateral aceito: `relatorios/relatorio_ocupacao.py` (somente leitura) passa a ver o slot de volta, sem alteração.
- **`pacientes.py`**: hoje só busca por CPF. Adicionar `RepositorioPacientes.buscar_por_id(id)` (aditivo; índice `_por_id`) para obter nome/e-mail a partir de `Consulta.paciente_id`. `cadastrar`, `buscar_por_cpf` e `atualizar_contato` ficam intocados.
- **`notificacao.py`**: adicionar templates `cancelamento_sem_reembolso`, `cancelamento_reembolso_parcial`, `cancelamento_reembolso_total` em `TEMPLATES` (convenção do backend). Os templates precisam de `{valor}`, então `Notificador.notificar` ganha `extras: dict | None = None` (parâmetro opcional, passado ao `format`); chamadas atuais seguem válidas.
- **Migração (`scripts/migracao/`)**: não usa disponibilidade; sem impacto. Nada de `--aplicar`.
- **`config/horarios-*.json`**: não são alterados.

## Novos módulos e arquivos

Em `backend/agendamento/` (nomes em português sem acento, `ValueError`/`KeyError` conforme convenção):

- `consultas.py`: `EstadoConsulta` (`AGENDADA`, `CANCELADA`, `REALIZADA`), `@dataclass Consulta` (id, paciente_id, medico_id, inicio, valor_centavos, pagamento_ref, estado, cancelada_em, reembolso_centavos), `RepositorioConsultas` em memória (`registrar`, `buscar`, `agendar(agenda, ...)` que chama `agenda.reservar` e cria a consulta).
- `pagamento.py`: `Protocol GatewayPagamento.reembolsar(pagamento_ref, valor_centavos, chave_idempotencia) -> str`, exceção `ErroGateway`, e `GatewayFake` (registra chamadas e permite simular falha), análogo ao `CanalConsole`.
- `reembolso.py`: função pura `calcular_reembolso(inicio, agora, valor_centavos) -> (percentual, valor_centavos)` e constantes de prazo.
- `cancelamento.py`: `ServicoCancelamento` (agenda, consultas, pacientes, gateway, notificador, relogio) e `ResultadoCancelamento`.

Fora de `backend/agendamento/`:

- `specs/cancelamento-reembolso.md`: spec derivada deste plano (primeiro entregável).
- `backend/tests/test_cancelamento.py`: testes novos (arquivo separado para não inflar `test_modulos.py`).

Modificados (aditivos): `pacientes.py`, `notificacao.py`; `backend/CLAUDE.md` ganha uma linha sobre `consultas`/`pagamento` só se a squad aprovar.

## Casos de teste (`unittest`, datas fixas de nov/2026, sem `date.today()`)

Consulta-base: `med-1`, segunda 16/11/2026 08:00 (turno da manhã, slot existe), valor 10000 centavos.

`calcular_reembolso` (puro):
- 48h antes → 100% / 10000; exatamente 24h (15/11 08:00) → 100%.
- 23h59 antes → 50% / 5000; exatamente 2h (06:00) → 50%.
- 1h59 antes → 0%; 30 min antes → 0%.
- Valor ímpar (10001) com 50% → 5000 (arredonda para baixo).

`ServicoCancelamento`:
- Cancelamento com 100%: gateway recebe 10000 e a chave de idempotência; consulta `CANCELADA`; slot volta a aparecer em `slots_do_dia`; paciente notificado com template "total".
- Cancelamento com 50%: gateway recebe 5000; notificação "parcial" com o valor.
- Cancelamento < 2h: gateway **não** chamado; slot liberado; notificação "sem reembolso".
- Duplicado: segunda chamada levanta `ValueError`; gateway chamado uma única vez; uma única notificação.
- Inexistente: `KeyError`; nada chamado.
- Já realizada (`agora` posterior ao `inicio`): `ValueError`; slot continua reservado; sem gateway.
- Falha no gateway: `ErroGateway`; consulta continua `AGENDADA`; slot continua reservado (`reservar` do mesmo horário ainda dá `ValueError`); sem notificação; novo `cancelar` com gateway recuperado funciona e estorna uma vez.
- Falha no canal de notificação: cancelamento e reembolso concluídos; sem exceção.
- Consulta sem valor/pagamento: sem chamada ao gateway.
- Reagendamento: após cancelar, `agenda.reservar` do mesmo slot funciona.
- Regressão: `buscar_por_id` em pacientes; `notificar` antigo (`confirmacao`) segue passando sem `extras`.

## Verificação

1. `python3 -m unittest discover -s backend/tests -t backend` (suíte completa, incluindo os testes antigos).
2. Teste isolado: `cd backend && python3 -m unittest tests.test_cancelamento`.
3. `python3 relatorios/relatorio_ocupacao.py` continua rodando (confirma que a interface pública não quebrou).
4. Rodar `/revisar-spec` (ou o subagente `revisor-spec`) antes do PR. Obs.: `SPEC.md` não existe, então o revisor só terá `specs/cancelamento-reembolso.md` como referência.
5. Ao final, mostrar `git diff --stat` (preferência do `CLAUDE.local.md`). Sem `git push`.

## Premissas para confirmar

1. Exatamente 2h conta como 50% (e não 0%).
2. Cancelar a < 2h é permitido (sem reembolso), em vez de ser bloqueado.
3. Falha no gateway **aborta** o cancelamento (consistência) em vez de cancelar e deixar o reembolso pendente numa fila.
4. Valores em centavos inteiros, com arredondamento para baixo no 50%.
5. Criar a entidade `Consulta` (hoje inexistente) faz parte deste escopo.
