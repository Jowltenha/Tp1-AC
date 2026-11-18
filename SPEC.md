# SPEC.md: Serviço de Agendamento de Consultas

| Campo | Valor |
|---|---|
| Versão | 1.0 |
| Status | Aprovada (baseline do TP) |
| Fonte da verdade para | Comportamento do serviço. Código que diverge desta spec é bug, a menos que a spec seja atualizada no mesmo PR |
| Specs detalhadas | `specs/<funcionalidade>.md`, uma por funcionalidade, quando a funcionalidade passa pelo plan mode |

## 1. Objetivo do serviço

Substituir o sistema legado de agendamento de consultas médicas por um serviço que:

- mostre os horários livres de cada médico a partir das configurações de turno;
- mantenha o cadastro dos pacientes;
- permita cancelar consultas com reembolso automático;
- avise o paciente de cada mudança.

## 2. Convenções desta spec

- Cada funcionalidade tem o ID **`SPEC-Fn`**. Os artefatos derivados (`TASK.md`, `AGENT.md`, `TOOLS.md`, PRs) citam a seção, por exemplo `SPEC.md §3.3`, em vez de copiar o conteúdo.
- Os critérios de aceite são numerados **`Fn-CAm`**, e cada um precisa de ao menos um teste automatizado.
- "Código afetado" cita `arquivo` e símbolo existentes no commit `a9856ba` ou nos commits seguintes.

---

## 3. Funcionalidades

### 3.1 `SPEC-F1`: Consulta de horários disponíveis

**Objetivo:** mostrar à recepção e ao paciente os horários livres de um médico em uma data, de acordo com os turnos configurados.

| | |
|---|---|
| **Entradas** | `medico_id: str` e `dia: date`. Configuração: todos os `config/horarios-*.json` |
| **Saídas** | `list[datetime]` ordenada com os inícios de slot livres. Não inclui os horários em `pausas` nem os já reservados |
| **Erros** | Arquivo de turno inválido: o serviço **não sobe**, e o erro diz o arquivo e a chave com problema |

**Critérios de aceite**

- **F1-CA1.** Segunda-feira 16/11/2026 tem 8 slots de manhã (08:00–11:30, de 30 em 30 min) e 5 à tarde (13:30, 14:15, 15:00, 16:30, 17:15, de 45 em 45 min, pulando a pausa de 15:45 a 16:00).
- **F1-CA2.** Um slot reservado some da lista. Depois de `liberar`, ele volta.
- **F1-CA3.** Os dois formatos de arquivo de turno (manhã e tarde) são aceitos. Um arquivo que não segue nenhum dos dois é rejeitado por `validar_turno` com a lista de erros.
- **F1-CA4.** Sábado e domingo não têm slots enquanto nenhum turno listar esses dias.

**Código afetado**

| Arquivo / símbolo | Relação |
|---|---|
| `backend/agendamento/disponibilidade.py` → `AgendaDisponibilidade.slots_do_dia`, `reservar`, `liberar` | **Implementa** esta funcionalidade |
| `backend/agendamento/disponibilidade.py` → `normalizar_turno`, `carregar_agenda` | **Implementa** a leitura dos dois formatos |
| `backend/agendamento/validacao_config.py` → `validar_turno` | **Implementa** o F1-CA3. **Falta** chamá-la em `carregar_agenda` para que o serviço não suba com um arquivo inválido |
| `config/horarios-manha.json`, `config/horarios-tarde.json` | Dados de entrada |
| `relatorios/relatorio_ocupacao.py` | **Consome** `slots_do_dia` (somente leitura) |

**Dúvida de negócio em aberto:** a sexta-feira à tarde não tem slots porque `horarios-tarde.json` tem `dias_semana: [1,2,3,4]` (veja `docs/ex05-sessoes-e-referencias.md`). O tech lead precisa confirmar se isso é intencional antes de mudar a configuração.

---

### 3.2 `SPEC-F2`: Cadastro de pacientes

**Objetivo:** cadastrar e manter os dados de contato dos pacientes, garantindo um CPF único e válido. Essa funcionalidade também é a porta de entrada da migração do legado.

| | |
|---|---|
| **Entradas** | `nome`, `cpf` (com ou sem máscara), `email`, `telefone` opcional |
| **Saídas** | `Paciente(id, nome, cpf só com dígitos, email, telefone)` |
| **Erros** | `ValueError` para CPF inválido, e-mail inválido, CPF duplicado ou telefone vazio. `KeyError` para paciente não encontrado |

**Critérios de aceite**

- **F2-CA1.** `529.982.247-25` e `52998224725` representam o mesmo paciente. Cadastrar o segundo depois do primeiro dá `ValueError`.
- **F2-CA2.** CPFs com todos os dígitos iguais ou com dígito verificador errado são rejeitados.
- **F2-CA3.** `atualizar_contato` com `telefone=""` dá `ValueError`, e com `telefone=None` mantém o telefone atual.
- **F2-CA4.** O paciente pode ser buscado por `id`, o que é necessário para o F3.
- **F2-CA5.** A migração do legado em dry-run com `scripts/migracao/exemplo_legado.csv` mostra `lidos=3, migrados=2, rejeitados=1`.

**Código afetado**

| Arquivo / símbolo | Relação |
|---|---|
| `backend/agendamento/pacientes.py` → `RepositorioPacientes.cadastrar`, `buscar_por_cpf`, `atualizar_contato`, `cpf_valido`, `_so_digitos` | **Implementa**. A interface pública não pode mudar |
| `backend/agendamento/pacientes.py` → `atualizar_contato` | **Muda:** falta a validação de telefone vazio do F2-CA3 |
| `backend/agendamento/pacientes.py` → *(novo)* `buscar_por_id` | **Adiciona** o F2-CA4 |
| `scripts/migracao/migrar_pacientes_legado.py` → `migrar` | **Consome** `cadastrar`. O F2-CA5 mede essa integração |

---

### 3.3 `SPEC-F3`: Cancelamento de consulta com reembolso automático

**Especificação completa:** [`specs/cancelamento-reembolso.md`](specs/cancelamento-reembolso.md), gerada em plan mode no Exercício 6. Aqui fica só o resumo que os artefatos derivados citam.

**Objetivo:** cancelar uma consulta agendada, devolver o horário à agenda e estornar o valor de acordo com a antecedência, sem intervenção manual.

| | |
|---|---|
| **Entradas** | `consulta_id: str`, `solicitante: str`. Relógio injetado |
| **Saídas** | `ResultadoCancelamento(consulta_id, percentual, reembolso_centavos, estorno_ref)` |
| **Regra** | Antecedência de 24h ou mais: 100%. De 2h a menos de 24h: 50%. Menos de 2h: 0% (`specs/cancelamento-reembolso.md §4`) |
| **Erros** | `KeyError` para consulta inexistente, `ValueError` para consulta já realizada, `ErroGateway` para falha no estorno (nesse caso nada é alterado). Um cancelamento duplicado é idempotente e não gera erro |

**Critérios de aceite:** são os **CA1 a CA13** de `specs/cancelamento-reembolso.md §7`, referenciados aqui como F3-CA1 a F3-CA13.

**Código afetado**

| Arquivo / símbolo | Relação |
|---|---|
| `backend/agendamento/disponibilidade.py` → `AgendaDisponibilidade.liberar` | **Consome**, sem mudança |
| `backend/agendamento/pacientes.py` → `buscar_por_id` | **Depende** do F2-CA4 |
| `backend/agendamento/notificacao.py` → `TEMPLATES`, `Notificador.notificar` | **Muda:** 3 templates novos e o parâmetro opcional `extras` |
| *(novos)* `consultas.py`, `pagamento.py`, `reembolso.py`, `cancelamento.py` | **Adiciona.** Hoje não existe entidade "consulta": a reserva em `AgendaDisponibilidade.reservados` não guarda paciente nem valor |

---

### 3.4 `SPEC-F4`: Notificação ao paciente

**Objetivo:** avisar o paciente sobre confirmação, lembrete e cancelamento de consulta, por um canal que pode ser trocado.

| | |
|---|---|
| **Entradas** | `tipo` (chave de `TEMPLATES`), `destino`, `nome`, `quando`, `extras` opcional (por exemplo `valor` no cancelamento) |
| **Saídas** | O texto da mensagem enviada. Efeito: `Canal.enviar(destino, mensagem)` |
| **Erros** | `ValueError` para tipo desconhecido. `KeyError` para um template que precisa de um parâmetro que não foi passado. Falhas do canal são repassadas para quem chamou, e é quem chamou que decide se a falha é crítica (no F3 não é) |

**Critérios de aceite**

- **F4-CA1.** A data aparece no formato `dd/mm/aaaa HH:MM`.
- **F4-CA2.** Um tipo desconhecido dá `ValueError` e nada é enviado.
- **F4-CA3.** Os templates de cancelamento mostram o valor reembolsado como `R$ 50,00`, a partir de `extras={"valor_centavos": 5000}` (contrato em `specs/cancelamento-reembolso.md §6.3`).
- **F4-CA4.** As chamadas sem `extras` (confirmação e lembrete) continuam funcionando.

**Código afetado**

| Arquivo / símbolo | Relação |
|---|---|
| `backend/agendamento/notificacao.py` → `Notificador`, `TEMPLATES`, `CanalConsole`, `Canal` | **Implementa** |
| `backend/agendamento/notificacao.py` → `Notificador.notificar` | **Muda:** recebe `extras` para o F4-CA3 e o F4-CA4 |

---

## 4. Requisitos transversais

- Python 3.11+ e biblioteca padrão, sem dependências de terceiros (política nível 1).
- Nenhum dado real de paciente em testes, logs ou commits (LGPD).
- Os testes usam datas fixas e relógio injetado, nunca `date.today()`.

## 5. Riscos de divergência entre spec e implementação

| # | Situação de divergência | Como aparece | Como o time reconcilia |
|---|---|---|---|
| R1 | **A implementação "melhora" a regra sem atualizar a spec.** Exemplo: o agente decide que cancelar com menos de 2h deve ser **bloqueado**, em vez de permitido sem reembolso, porque "faz mais sentido" | O teste do F3-CA3 falha, ou é alterado no mesmo PR para passar | **A spec vence por padrão.** Um PR que altera um teste ligado a um `Fn-CAm` precisa alterar a spec junto, e o tech lead aprova as duas mudanças. Se a mudança não for aprovada, o código volta a seguir a spec. A skill `/revisar-spec` e o subagente `revisor-spec` apontam "escopo extra" antes do PR |
| R2 | **O código existente contradiz uma premissa da spec.** Exemplo: a spec supõe que existe "consulta", mas `reservados` só guarda `(medico_id, datetime)`. Ou a spec supõe um formato único de turno quando há dois | O implementador ou o agente não consegue cumprir o critério sem mudar algo fora do escopo | O implementador **para e abre uma pendência na spec**, sem improvisar. A spec ganha uma seção "Contexto do código atual", como a `§2` em `specs/cancelamento-reembolso.md`, e a decisão é registrada antes de continuar. Esse é o mesmo princípio de "Fonte da verdade" do `CLAUDE.md` |
| R3 | **A configuração muda e a spec, não.** Exemplo: alguém inclui a sexta em `dias_semana` e o F1-CA1 deixa de descrever a realidade | Testes com números fixos de slots falham depois de uma mudança em `config/` | Uma mudança em `config/horarios-*.json` exige aprovação humana e atualização dos critérios do F1 no mesmo PR. `validar_turno` impede formatos novos sem atualização da spec |
| R4 | **Um critério passa no teste, mas o comportamento real diverge.** Exemplo: o gateway falso aceita qualquer chamada e o gateway real rejeita a chave de idempotência | Problema que aparece só em homologação | A spec do gateway real (fora de escopo da v1.0) vai incluir testes de contrato. Até lá, o F3 só vai para produção com o gateway real atrás de uma feature flag, depois de um teste manual registrado no PR |
