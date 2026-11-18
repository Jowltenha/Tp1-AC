# Onboarding: Claude Code na squad de Agendamento

**Para:** desenvolvedores da squad de agendamento de consultas que vão usar o Claude Code pela primeira vez.
**Objetivo:** deixar claro quando usar o Claude Code, o que ele faz de verdade e o que nunca deve ser delegado a ele sem um humano revisando.

O Claude Code não é um autocomplete. Ele é um agente que lê o repositório, executa comandos, edita arquivos e confere o próprio trabalho. Por isso ele economiza tempo em tarefas de várias etapas e também pode causar estrago se receber permissões que não deveria. Para cada capacidade, a tabela mostra um caso em que **usar** é o certo e um caso que **exige supervisão humana direta**.

## 1. Capacidades e quando usá-las

| # | Capacidade | Usar no dia a dia da squad | Não usar sem supervisão humana direta |
|---|---|---|---|
| 1 | **Ler e escrever arquivos** (Read / Write) | Ler `backend/agendamento/disponibilidade.py` e os dois `config/horarios-*.json` antes de explicar por que um slot não aparece na agenda; criar uma spec nova em `specs/`. | Alterar `config/horarios-*.json` que já estão em uso pelas clínicas. Uma chave errada tira os horários do ar. A mudança vai em PR e alguém do time revisa. |
| 2 | **Executar comandos de shell** (Bash) | Rodar `python3 -m unittest discover -s backend/tests -t backend` depois de cada mudança; rodar a migração em **dry-run** para ver quantas linhas do legado seriam rejeitadas. | Rodar `migrar_pacientes_legado.py --aplicar` ou qualquer migração de banco em produção, `git push`, apagar dados. No projeto, `--aplicar` e `git push` estão em `deny` no `.claude/settings.json`. |
| 3 | **Buscar no código** (Grep / Glob) | Antes de mudar a assinatura de `RepositorioPacientes.cadastrar`, encontrar todos os pontos que a chamam (backend, `scripts/migracao/`, `relatorios/`). | Usar a busca como prova de que "nada mais usa isso" antes de **remover** uma interface. A busca textual não encontra chamadas dinâmicas nem consumidores fora do repositório. Quem decide a remoção é uma pessoa. |
| 4 | **Edição orientada por diff** (Edit) | Refatorações pequenas e localizadas, como extrair `_so_digitos` em `pacientes.py`. O diff aparece para revisão antes de ser aceito. | Aceitar em lote dezenas de edições de uma refatoração ampla (por exemplo, trocar o repositório em memória por persistência real) sem ler cada diff. O modo de auto-aceite de edições não deve ficar ligado nessas tarefas. |
| 5 | **Skills** (`.claude/skills/`) | Rodar `/revisar-spec specs/cancelamento-reembolso.md` antes de abrir o PR, para que toda spec seja revisada com o mesmo checklist. | Tratar o veredito "PRONTA PARA IMPLEMENTAÇÃO" da skill como aprovação. A skill aponta problemas, mas quem aprova a spec é o tech lead. |
| 6 | **Subagentes** (`.claude/agents/`, ferramenta Agent) | Pedir ao subagente `revisor-spec` uma revisão independente do diff de cancelamento. Ele começa com contexto limpo e não herda as suposições da sessão que escreveu o código. | Delegar a um subagente uma **decisão de arquitetura** (por exemplo, escolher o gateway de pagamento do reembolso) e aplicar o resultado direto. O subagente entrega um resumo, e o raciocínio dele não fica visível. |
| 7 | **Plan mode** (Shift+Tab duas vezes, ou `/plan`) | Planejar uma funcionalidade nova, como o cancelamento com reembolso, sem tocar no código, e transformar o plano em uma spec versionada para o time revisar. | Aprovar o plano e mandar executar na mesma hora quando ele mexe em dinheiro (reembolso) ou em dados de pacientes. Nesses casos o plano passa por revisão de outra pessoa antes. |
| 8 | **Memória de projeto** (`CLAUDE.md` em camadas, `@arquivo`) | Registrar armadilhas reais do projeto, como "os dois arquivos de turno têm formatos diferentes", para que todas as sessões já comecem sabendo disso. | Colocar no `CLAUDE.md` regras de segurança que dependem só do modelo obedecer. Regra que não pode ser quebrada vai em `permissions.deny` (que é aplicado pela ferramenta) ou na política gerenciada (nível 1). |

## 2. Regras práticas

1. **O Claude Code propõe e um humano aprova** tudo o que é irreversível ou que sai do repositório: produção, `push`, dados de pacientes, dinheiro.
2. **Peça que ele leia antes de supor.** Use `@config/horarios-tarde.json` em vez de descrever o formato de memória.
3. **Uma tarefa por sessão.** Ao trocar de assunto, use `/clear`. Sessões longas acumulam suposições antigas (veja o Exercício 4).
4. **Verifique sempre.** Peça para ele rodar os testes, e leia o resultado você mesmo.

## 3. O que foi configurado e testado

| Item | Onde | Verificação feita |
|---|---|---|
| Claude Code instalado | CLI 2.1.260 (Windows/npm) e 2.1.281 (extensão VS Code no WSL) | `claude --version` retornou `2.1.281 (Claude Code)` |
| Repositório Git do serviço | `TP1-AC/`, com `README.md` inicial | `git log` mostra os commits do TP |
| Sessão real funcionando | headless `claude -p` na pasta do projeto | Pedido "liste os arquivos da pasta config" respondido com uma chamada de ferramenta: *"A pasta `config` tem dois arquivos: `horarios-manha.json` e `horarios-tarde.json`."* |
| Permissões do projeto | `.claude/settings.json` | `allow` para testes, `git diff/status/log` e edição em `backend/`; `ask` para migração, commit e edição de `config/`, das specs e dos módulos existentes; `deny` para `--aplicar`, `git push`, acesso à web e `.env`. Na primeira execução, a CLI avisou que ignora `allow` em pasta não confiável ("this workspace has not been trusted"). Por isso é preciso aceitar o *trust dialog* uma vez, de forma interativa |
| Skill do projeto | `.claude/skills/revisar-spec/SKILL.md` | A skill aparece na lista de skills disponíveis da sessão |
| Subagente do projeto | `.claude/agents/revisor-spec.md` | Só tem ferramentas de leitura e de teste; não pode editar |
| Testes do projeto | `backend/tests/` | `python3 -m unittest discover -s backend/tests -t backend`: `Ran 7 tests ... OK` |

## 4. Por que o ambiente está pronto para os próximos artefatos

O ambiente está pronto porque cada parte do que os próximos exercícios exigem foi configurada e testada, e não apenas instalada. O Claude Code roda dentro do repositório Git do serviço e respondeu a uma sessão real que precisou usar ferramentas para ler o projeto, o que confirma que ele acessa e enxerga os arquivos certos. A suíte de testes roda com um único comando já liberado em `allow`, e assim toda spec poderá ser conferida contra o código de verdade. As operações perigosas que este documento lista como "não usar sem supervisão" estão bloqueadas pela própria ferramenta (`deny` para `--aplicar` e `git push`; `ask` para migração e commit), em vez de dependerem só da disciplina de cada pessoa. A skill `revisar-spec` e o subagente `revisor-spec` já estão versionados em `.claude/`, então qualquer colega que clonar o repositório recebe o mesmo fluxo de revisão. Com isso, os artefatos de especificação (CLAUDE.md, SPEC.md, AGENT/TASK/TOOLS) podem ser escritos, revisados e testados com o mesmo ferramental por todo o time.
