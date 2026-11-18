# Exercícios 7 e 8: SPEC.md e artefatos AGENT / TASK / TOOLS

## Exercício 7: `SPEC.md`

O arquivo [`SPEC.md`](../SPEC.md) tem **quatro** funcionalidades. Cada uma tem **objetivo, entradas, saídas, erros e critérios de aceite numerados** (`Fn-CAm`), e também uma tabela **"Código afetado"** que aponta arquivo e símbolo existentes:

| ID | Funcionalidade | Principal código afetado | Tipo de impacto |
|---|---|---|---|
| `SPEC-F1` | Consulta de horários disponíveis | `disponibilidade.py` (`slots_do_dia`, `normalizar_turno`), `validacao_config.py` | Implementa. Falta ligar `validar_turno` a `carregar_agenda` |
| `SPEC-F2` | Cadastro de pacientes | `pacientes.py` (`cadastrar`, `atualizar_contato`), `scripts/migracao/` | Implementa. Muda `atualizar_contato` e adiciona `buscar_por_id` |
| `SPEC-F3` | **Cancelamento com reembolso** (do Ex. 6) | `disponibilidade.liberar`, `pacientes.buscar_por_id`, `notificacao.TEMPLATES` e 4 módulos novos | Consome, muda e adiciona. Resumo no `SPEC.md`, detalhe em `specs/` |
| `SPEC-F4` | Notificação ao paciente | `notificacao.py` (`Notificador.notificar`) | Implementa. Muda `notificar` com o parâmetro `extras` |

A seção **§5 Riscos** descreve quatro situações de divergência:

- **R1:** o agente "melhora" a regra por conta própria.
- **R2:** o código contradiz uma premissa da spec.
- **R3:** a configuração muda e a spec não acompanha.
- **R4:** o dublê de teste passa e o sistema real falha.

Para cada uma, a seção diz como a divergência aparece e qual é o procedimento de reconciliação. A regra geral é que **a spec vence por padrão**, e mudar um critério exige mudar a spec no mesmo PR com aprovação do tech lead.

**Como os dois níveis se relacionam:** o `SPEC.md` é o documento do serviço inteiro. Quando uma funcionalidade passa pelo plan mode, ela ganha um arquivo detalhado em `specs/`, e o `SPEC.md` passa a ter só o resumo e o link. Foi o que aconteceu com o F3, para que o mesmo conteúdo não fique escrito em dois lugares.

## Exercício 8: `AGENT.md`, `TASK.md`, `TOOLS.md`

| Artefato | Responde à pergunta | Referências ao SPEC |
|---|---|---|
| [`AGENT.md`](../AGENT.md) | **Quem** executa, com que papel e com que limites, e quando deve parar | `SPEC.md §3.3` (escopo), `§5` R1/R2 (quando escalar), `specs/…§8` (fora de escopo) |
| [`TASK.md`](../TASK.md) | **O que** fazer, em que ordem e quando a tarefa está pronta | Cada passo cita `§3`, `§4`, `§5`, `§6` ou `§7` da spec. A definição de pronto é "F3-CA1 a F3-CA13, F2-CA4, F4-CA3 e F4-CA4 com teste" |
| [`TOOLS.md`](../TOOLS.md) | **Com o quê**: ferramentas do Claude Code e módulos, com o nível de acesso de cada um | A tabela de módulos vem da seção "Código afetado" do `SPEC.md §3.3` e cita `§3.1`, `§3.2` e `§3.4` para cada módulo existente |

Nenhum dos três copia regra de negócio. O `TASK.md`, por exemplo, diz "Criar `calcular_reembolso`, cumpre `specs/cancelamento-reembolso.md §4`" e **não** repete os percentuais 100/50/0. Se o prazo mudar, a mudança acontece em um único lugar.

### Por que três arquivos separados e persistentes

Cada arquivo muda por um motivo diferente, em um ritmo diferente, e cada um é lido por pessoas diferentes. Com tudo em um documento só, qualquer mudança obrigaria todo mundo a reler e revalidar o documento inteiro. O `AGENT.md` descreve um **papel** que dura mais que uma tarefa. Quando o `TASK-F3-01` terminar, o mesmo `AGENT-impl-cancelamento` pode receber um `TASK-F3-02` (por exemplo, integrar o gateway real) sem que ninguém reescreva os limites dele. O `TASK.md` é **descartável e específico**: nasce de uma seção do `SPEC.md`, é executado e fechado, e o próximo desenvolvedor da squad só precisa escrever um novo `TASK.md`, reaproveitando o agente e as ferramentas. O `TOOLS.md` corresponde ao que está configurado de fato em `.claude/settings.json`. Por isso é o arquivo que a segurança e o tech lead revisam, e mudar uma permissão não deve exigir mexer na descrição da tarefa. Arquivos separados também fazem o histórico do git e os PRs mostrarem com precisão **o que** mudou: um diff em `TOOLS.md` é uma mudança de permissão, e um diff em `TASK.md` é uma mudança de escopo. Isso não fica escondido no meio de um documento grande. Para os agentes automatizados, a separação permite carregar na janela de contexto só o necessário (a estratégia *Select* do Exercício 4). Um subagente revisor, por exemplo, lê `TASK.md` e `SPEC.md §3.3`, mas não precisa do `TOOLS.md`. E como os três são arquivos versionados no repositório, e não texto de conversa, qualquer desenvolvedor ou sessão nova do Claude Code chega ao mesmo contexto depois de um `git pull`, sem depender da memória de quem escreveu.
