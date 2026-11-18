# Spec: Cancelamento de consulta com reembolso automático

| Campo | Valor |
|---|---|
| ID | `SPEC-F3` (seção 3.3 do [`SPEC.md`](../SPEC.md)) |
| Versão | 1.2. Incorpora duas rodadas do checkpoint 1 (`/revisar-spec`, sessões `34d4e4a3` e `60e352f9`), registradas em [`docs/evidencias/ex09-revisar-spec.md`](../docs/evidencias/ex09-revisar-spec.md) |
| Status | Revisada pelo checkpoint 1. Aguarda aprovação do tech lead (etapa 3 do fluxo) antes de virar a `TASK-F3-01` |
| Origem | Plano gerado pelo Claude Code em **plan mode** (sessão `870d4f97`), guardado em [`docs/evidencias/ex06-plano-plan-mode.md`](../docs/evidencias/ex06-plano-plan-mode.md) |
| Altera | `backend/agendamento/pacientes.py`, `notificacao.py` (só adições) |
| Consome sem alterar | `backend/agendamento/disponibilidade.py` (`reservar`, `liberar`) |
| Cria | `backend/agendamento/consultas.py`, `pagamento.py`, `reembolso.py`, `cancelamento.py` |

## 1. Objetivo

Permitir que o paciente (ou a recepção, em nome dele) cancele uma consulta agendada. Ao cancelar, o horário volta para a agenda e o reembolso proporcional à antecedência é calculado e estornado automaticamente. Ninguém precisa fazer estorno manual.

## 2. Contexto do código atual

- Hoje **não existe a entidade "consulta"**. `AgendaDisponibilidade.reservados` guarda só `(medico_id, datetime)` e não tem paciente, valor pago nem estado. Esta spec cria essa entidade (§6.1).
- `AgendaDisponibilidade.liberar(medico_id, inicio)` já existe e é idempotente (usa `set.discard`). `reservar` faz *check-then-add* **sem lock**, e a proteção contra concorrência fica em `RepositorioConsultas` (§6.1).
- Não existe integração de pagamento. A spec define uma porta (`GatewayPagamento`) e um dublê de teste.
- O backend não usa `logging` hoje. Esta spec cria o primeiro logger (§5, B6).
- `relatorios/relatorio_ocupacao.py` cria a própria agenda com `carregar_agenda()`, sem reservas. Por isso **não é afetado** por reservas nem por cancelamentos.

## 3. Comportamento esperado

Interface: `ServicoCancelamento.cancelar(consulta_id: str, solicitante: str) -> ResultadoCancelamento`

`solicitante` é **só para auditoria**: identifica quem pediu o cancelamento (`"paciente:<id>"` ou `"recepcao:<usuario>"`) e é gravado em `Consulta.cancelada_por`. Esta versão não faz controle de autorização (fora de escopo, §8). Num cancelamento duplicado (B2), o `solicitante` da segunda chamada é ignorado.

Fluxo, sempre nesta ordem. O lock da consulta é mantido **do passo 2 ao passo 6**:

1. **Localizar** a consulta em `RepositorioConsultas`. Se não existir: B3.
2. **Obter o lock** da consulta (§5, B8).
3. **Validar o estado**, nesta ordem:
   1. Se o estado for `CANCELADA`, devolver o `ResultadoCancelamento` gravado (B2) e encerrar.
   2. Se o estado for `REALIZADA` ou se `inicio <= agora`: B4.
4. **Definir o reembolso**, nesta ordem:
   1. Se a consulta já tem `reembolso_pendente_centavos` (deixado por uma tentativa anterior que falhou no gateway), **reutilizar** esse valor e o percentual gravado. Não recalcular (B5).
   2. Se não, e se `valor_centavos == 0` ou `pagamento_ref is None`, o percentual e o reembolso são **0** (B7).
   3. Nos outros casos, usar `calcular_reembolso(inicio, agora, valor_centavos)` (§4).
5. Se o reembolso for maior que zero:
   1. Gravar `reembolso_pendente_centavos` e `percentual_reembolso` na consulta. O estado continua `AGENDADA`.
   2. Chamar `gateway.reembolsar(pagamento_ref, valor, chave_idempotencia=consulta_id)`.
6. **Concluir:**
   1. Gravar o estado `CANCELADA` com `cancelada_em`, `cancelada_por`, `percentual_reembolso`, `reembolso_centavos`, `estorno_ref` e `resultado`, e limpar `reembolso_pendente_centavos`.
   2. **Liberar o slot** com `agenda.liberar(medico_id, inicio)`.
   3. Liberar o lock.
7. **Notificar** o paciente com o template correspondente ao percentual (§6.3). Essa etapa é de melhor esforço (B6).
8. **Retornar** o `ResultadoCancelamento`.

O relógio é **injetado** (`relogio: Callable[[], datetime]`) para que os testes usem datas fixas. Os datetimes são *naive*, no horário local da clínica. O mesmo objeto `AgendaDisponibilidade` é passado a `RepositorioConsultas.agendar` e ao `ServicoCancelamento`.

## 4. Regra de reembolso

| Antecedência (`inicio - agora`) | Percentual | Gateway chamado? |
|---|---|---|
| `>= 24h` | 100% | Sim |
| `>= 2h` e `< 24h` | 50% | Sim |
| `< 2h` (fora do prazo de reembolso), inclusive valores negativos | 0% | Não |

- Os limites são **fechados à esquerda**: exatamente 24h dá 100%, e exatamente 2h dá 50%.
- Os valores são em **centavos inteiros**. O de 50% arredonda **para baixo** (`valor * 50 // 100`).
- `calcular_reembolso` é uma função pura e **não valida** a entrada. Quem chama garante `valor_centavos >= 0`, e o caso `agora >= inicio` já é barrado em B4.
- Os limites e percentuais ficam como constantes em `reembolso.py` (`PRAZO_TOTAL = 24h`, `PRAZO_PARCIAL = 2h`).

## 5. Condições de borda

| # | Situação | Comportamento | Erro |
|---|---|---|---|
| B1 | Cancelamento **fora do prazo** (< 2h) | Cancelamento **permitido**. Reembolso de 0, gateway não chamado, slot liberado, paciente recebe a notificação `cancelamento_sem_reembolso` | — |
| B2 | Cancelamento **duplicado** (a consulta já está `CANCELADA`, mesmo que o `inicio` já tenha passado) | Devolve o **mesmo** `ResultadoCancelamento` gravado no passo 6, sem chamar o gateway e sem notificar de novo. Essa checagem vem **antes** de B4 | — (idempotente) |
| B3 | Consulta **inexistente** | Nada é alterado | `KeyError("Consulta não encontrada")` |
| B4 | Consulta **já realizada**: estado `REALIZADA`, ou `inicio <= agora` (inclui `inicio == agora`) | Nada é alterado e o slot continua como está | `ValueError("Consulta já realizada")` |
| B5 | **Falha no gateway** de pagamento (`ErroGateway`, inclusive timeout) | O estado continua `AGENDADA`, o slot continua reservado, nenhuma notificação é enviada e o erro é repassado. O valor fica gravado em `reembolso_pendente_centavos`, e o retry reutiliza **o mesmo valor e a mesma chave** (`consulta_id`), mesmo que já tenha passado para outra faixa de prazo. Assim, se a primeira tentativa chegou a estornar antes do timeout, o gateway reconhece a chave e não estorna de novo (§6.2) | `ErroGateway` |
| B6 | **Falha na notificação**: qualquer exceção no passo 7 (paciente não encontrado, erro de template, falha do canal) | Cancelamento e reembolso **ficam valendo**. A exceção é capturada e registrada no logger `agendamento.cancelamento`, nível `WARNING`, com a mensagem exata `"falha na notificacao consulta_id=%s erro=%s"` e os argumentos `consulta_id` e `type(exc).__name__`. A mensagem não leva nome, e-mail nem valor (LGPD, `SPEC.md §4`) | — |
| B7 | Consulta **sem pagamento** (`valor_centavos == 0` ou `pagamento_ref is None`) | Cancela normalmente, sem chamar o gateway. Percentual de 0, reembolso de 0, `estorno_ref = None` e template `cancelamento_sem_reembolso` | — |
| B8 | Dois pedidos de cancelamento **concorrentes** para a mesma consulta | O lock por consulta cobre do passo 2 ao 6, então um dos pedidos termina e o outro cai em B2. Os locks ficam num `dict[str, threading.Lock]` protegido por um lock global do repositório, que cria o lock de cada consulta sem corrida | — |

## 6. Pontos de integração e contratos

### 6.1 Módulos novos

**`consultas.py`**

```python
class EstadoConsulta(Enum): AGENDADA, CANCELADA, REALIZADA

@dataclass(frozen=True)
class ResultadoCancelamento:          # fica aqui para evitar import circular com cancelamento.py
    consulta_id: str
    percentual: int
    reembolso_centavos: int
    estorno_ref: str | None

@dataclass
class Consulta:
    id: str                           # uuid4, como em pacientes.py
    paciente_id: str
    medico_id: str
    inicio: datetime
    valor_centavos: int
    pagamento_ref: str | None
    estado: EstadoConsulta = EstadoConsulta.AGENDADA
    reembolso_pendente_centavos: int | None = None
    percentual_reembolso: int | None = None
    cancelada_em: datetime | None = None
    cancelada_por: str | None = None
    reembolso_centavos: int | None = None
    estorno_ref: str | None = None
    resultado: ResultadoCancelamento | None = None

class RepositorioConsultas:
    def agendar(self, agenda, paciente_id, medico_id, inicio, valor_centavos, pagamento_ref) -> Consulta
        # sob o lock global do repositório: agenda.reservar(...) e depois cria a Consulta.
        # ValueError se o slot estiver indisponível.
    def buscar(self, consulta_id: str) -> Consulta   # KeyError("Consulta não encontrada")
    def lock(self, consulta_id: str) -> threading.Lock
```

**`pagamento.py`**: segue o padrão de `notificacao.py`, em que a porta e o dublê ficam no mesmo módulo.

```python
class ErroGateway(Exception): ...

class GatewayPagamento(Protocol):
    def reembolsar(self, pagamento_ref: str, valor_centavos: int, chave_idempotencia: str) -> str: ...

class GatewayFake:
    falhar_proximas: int = 0                      # cada chamada que falha consome 1 e NÃO registra estorno
    estornar_e_falhar_proxima: bool = False       # simula timeout: registra o estorno e levanta ErroGateway
    ao_reembolsar: Callable[[], None] | None      # gancho chamado dentro de reembolsar (sincroniza threads no CA12)
    estornos: dict[str, tuple[int, str]]          # chave -> (valor, estorno_ref); protegido por lock interno
```

**`reembolso.py`**

```python
def calcular_reembolso(inicio: datetime, agora: datetime, valor_centavos: int) -> tuple[int, int]
    # retorna (percentual, valor_centavos)
```

**`cancelamento.py`**

```python
class ServicoCancelamento:
    def __init__(self, agenda, consultas, pacientes, gateway, notificador,
                 relogio=datetime.now): ...
    def cancelar(self, consulta_id: str, solicitante: str) -> ResultadoCancelamento: ...
```

### 6.2 Contrato do gateway

1. Repetir uma chamada com a mesma `chave_idempotencia` devolve o **mesmo** `estorno_ref` e não estorna de novo, **mesmo que a chamada anterior tenha terminado em `ErroGateway`** (timeout depois de efetivar o estorno).
2. Uma chamada que termina em `ErroGateway` pode ou não ter efetivado o estorno. Quem chama deve repetir com a mesma chave e o mesmo valor (B5).
3. O `GatewayFake` (§6.1) implementa os itens 1 e 2. O contrato com o gateway real e a feature flag de liberação ficam para a spec do gateway (§8).

### 6.3 Módulos existentes

| Módulo | Uso | Mudança |
|---|---|---|
| `disponibilidade.py` | `reservar` (em `agendar`) e `liberar` (passo 6) | **Nenhuma** |
| `pacientes.py` | Buscar nome e e-mail a partir de `Consulta.paciente_id` | **Adição:** `RepositorioPacientes.buscar_por_id(id) -> Paciente | None` (mesmo padrão de `buscar_por_cpf`). O índice `_por_id` é criado no `__init__` e preenchido em `cadastrar`. `cadastrar`, `buscar_por_cpf` e `atualizar_contato` não mudam |
| `notificacao.py` | Avisar o paciente no passo 7 | **Adição** de três templates e do parâmetro `extras` (detalhes abaixo) |
| `config/horarios-*.json` | — | Não é alterado |
| `scripts/migracao/`, `relatorios/` | — | Sem impacto (veja §2) |

**Contrato da notificação**

- **Chamada:** `notificar(tipo, destino=paciente.email, nome=paciente.nome, quando=consulta.inicio, extras={"valor_centavos": reembolso})`.
- **`extras`:** `Notificador.notificar(..., extras: dict | None = None)` mescla `extras` nos parâmetros do `format`. Se houver `valor_centavos`, ele também gera `valor` no formato brasileiro, com milhar e dois decimais: `5000` vira `R$ 50,00` e `123456` vira `R$ 1.234,56`. Chamar sem `extras` continua funcionando (F4-CA4).
- **Escolha do template pelo percentual:** 100% usa `cancelamento_reembolso_total`, 50% usa `cancelamento_reembolso_parcial` e 0% usa `cancelamento_sem_reembolso`.

| Chave | Texto |
|---|---|
| `cancelamento_reembolso_total` | `"Olá, {nome}! Sua consulta de {quando} foi cancelada. Reembolso integral de {valor}."` |
| `cancelamento_reembolso_parcial` | `"Olá, {nome}! Sua consulta de {quando} foi cancelada. Reembolso parcial de {valor}."` |
| `cancelamento_sem_reembolso` | `"Olá, {nome}! Sua consulta de {quando} foi cancelada. Cancelamento fora do prazo: sem reembolso."` |

## 7. Critérios de aceite

Todos os critérios têm teste automatizado em `backend/tests/test_cancelamento.py`, usando a consulta-base `med-1` de segunda-feira 16/11/2026 às 08:00, com valor de 10000 centavos e `pagamento_ref="pag-1"`.

- [ ] **CA1.** Cancelando 48h antes, o gateway recebe 10000 e a chave `consulta_id`, a consulta vira `CANCELADA` com `cancelada_por` gravado, o slot de 08:00 volta a aparecer em `slots_do_dia` e a notificação usa `cancelamento_reembolso_total` com `R$ 100,00`.
- [ ] **CA2.** Cancelando exatamente 24h antes, o reembolso é de 100%. Cancelando 23h59 antes, é de 50% (5000), com o template `cancelamento_reembolso_parcial`.
- [ ] **CA3.** Cancelando exatamente 2h antes, o reembolso é de 50%. Cancelando 1h59 antes, é de 0%, o gateway **não** é chamado e a notificação enviada é `cancelamento_sem_reembolso` (B1).
- [ ] **CA4.** O valor 10001 com 50% dá 5000 (arredondamento para baixo).
- [ ] **CA5.** Uma segunda chamada a `cancelar` devolve um resultado igual ao primeiro, o gateway é chamado só uma vez no total e só uma notificação é enviada. O mesmo vale quando a segunda chamada acontece depois do `inicio` (B2 vem antes de B4).
- [ ] **CA6.** Uma consulta inexistente gera `KeyError`, e o gateway e o notificador não são chamados (B3).
- [ ] **CA7.** Cancelar com `agora == inicio`, com `agora > inicio` ou com o estado `REALIZADA` gera `ValueError`, e o slot continua reservado (B4).
- [ ] **CA8.** Com `falhar_proximas=1`, sai `ErroGateway`, a consulta continua `AGENDADA`, `reservar` do mesmo horário ainda falha e nenhuma notificação é enviada. Na segunda chamada, o gateway registra exatamente um estorno (B5).
- [ ] **CA9.** Com o canal de notificação falhando, ou com o paciente não encontrado, o cancelamento é concluído sem exceção. `assertLogs("agendamento.cancelamento", "WARNING")` captura a mensagem do B6, e ela não contém o e-mail nem o nome do paciente.
- [ ] **CA10.** Os 10 testes que já existiam continuam passando, e `python3 relatorios/relatorio_ocupacao.py` continua rodando.
- [ ] **CA11.** Uma consulta com `valor_centavos == 0`, e outra com `pagamento_ref is None` (valor 10000, 48h antes), são canceladas sem chamar o gateway, com percentual 0, `estorno_ref is None` e o template `cancelamento_sem_reembolso` (B7).
- [ ] **CA12.** Duas threads cancelando a mesma consulta, sincronizadas por um `threading.Barrier` e com `ao_reembolsar` segurando a primeira chamada dentro do gateway, geram uma única chamada ao gateway e resultados iguais (B8).
- [ ] **CA13.** Com `estornar_e_falhar_proxima=True` a 48h do início, a primeira chamada levanta `ErroGateway`. O retry feito 23h antes do início (outra faixa) reutiliza o valor de 10000 e a mesma chave, o gateway fica com **um** estorno de 10000 e o resultado mostra percentual 100 (B5).

## 8. Fora de escopo

- Integração com um gateway real (será outra spec). Ela vai cobrir o contrato real do §6.2, as credenciais geridas pela TI e a **feature flag** de liberação em produção (`SPEC.md §5`, R4).
- Autorização: quem pode cancelar a consulta de quem.
- Reembolso parcial definido manualmente pela recepção.
- Persistência em banco de dados. Os repositórios continuam em memória, como no resto do serviço.
- Tornar `AgendaDisponibilidade.reservar` thread-safe por conta própria. Nesta versão a proteção fica em `RepositorioConsultas.agendar`.
