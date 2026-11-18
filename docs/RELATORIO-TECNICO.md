# Relatório Técnico: TP Claude Code e Spec-Driven Development

**Projeto:** Serviço de Agendamento de Consultas Médicas
**Autor:** João Pedro Barboza
**Ambiente:** Claude Code 2.1.281 (extensão VS Code, binário Linux no WSL2) e 2.1.260 (CLI); Python 3.14; Git
**Data:** 18/11/2026

## Visão geral da entrega

Todos os exercícios foram feitos sobre **um único repositório Git** (`TP1-AC/`), que evolui em sequência: ambiente, código, `CLAUDE.md`, hierarquia, sessões, spec, artefatos e fluxo. Toda evidência de comportamento (Ex. 2, 4, 5, 6 e 9) vem de **sessões reais do Claude Code** executadas no projeto. As transcrições ficam em `docs/evidencias/`, incluindo os logs `.jsonl` brutos que o próprio Claude Code grava. As sessões com várias rodadas foram conduzidas pelo script [`docs/evidencias/rodar_sessao.sh`](evidencias/rodar_sessao.sh), que chama `claude -p` e encadeia as rodadas com `--resume <session_id>`. Um `/clear` no script inicia uma sessão nova, e as transcrições são gravadas sem edição.

Estado final verificado: `python3 -m unittest discover -s backend/tests -t backend` dá **10 testes, OK**.

---

## Exercício 1: Ambiente e onboarding

**Solução:**

- O repositório Git foi criado com `README.md` e estrutura de pastas.
- O Claude Code foi configurado no nível do projeto com:
  - `.claude/settings.json`, com permissões `allow` / `ask` / `deny`;
  - a skill `.claude/skills/revisar-spec`;
  - o subagente `.claude/agents/revisor-spec.md`.
- A instalação foi testada com `claude --version` e com uma sessão real que usou ferramenta para listar `config/`.
- O [`docs/onboarding-claude-code.md`](onboarding-claude-code.md) lista **8 capacidades**:
  - leitura e escrita de arquivos;
  - shell;
  - busca;
  - edição por diff;
  - skills;
  - subagentes;
  - plan mode;
  - memória em camadas.
- Para cada capacidade há um caso de uso da squad e um caso que exige supervisão humana direta.

**Decisão relevante:** as proibições do documento (`--aplicar`, `git push`) foram **aplicadas pela ferramenta**, em `permissions.deny`, e não ficaram só no texto. Assim o argumento de "ambiente pronto" se apoia no que foi configurado e testado.

## Exercício 2: `/init`

**Solução:**

- Foram criados os módulos `disponibilidade.py`, `pacientes.py` e `notificacao.py`, mais testes, configs e os subprojetos de migração e relatórios.
- O `/init` foi executado de verdade. A saída original ficou em [`docs/ex02/CLAUDE.init-gerado.md`](ex02/CLAUDE.init-gerado.md).

**Análise** ([`docs/ex02-analise-init.md`](ex02-analise-init.md)):

- **Acertos.** O `/init` acertou os fatos que estão no código:
  - os comandos de teste, inclusive como rodar um teste isolado;
  - a dependência entre as pastas por `sys.path`;
  - a tabela dos dois formatos de turno.
- **Lacunas.** Ficou de fora o que não está no código:
  - regras de segurança;
  - o processo da squad;
  - a divisão por escopo;
  - a definição de qual é a fonte da verdade.
- **Ajustes manuais.** Foram listados cinco, e todos foram aplicados no Ex. 3.

## Exercício 3: Hierarquia de cinco níveis

**Solução** ([`docs/ex03-hierarquia.md`](ex03-hierarquia.md)):

| Nível | Arquivo |
|---|---|
| 1. Política gerenciada | `hierarquia/nivel1-managed-policy/CLAUDE.md` (destino real: `/etc/claude-code/`) |
| 2. Usuário | `hierarquia/nivel2-usuario/CLAUDE.md` (destino real: `~/.claude/`) |
| 3. Projeto | `CLAUDE.md` |
| 4. Projeto local | `CLAUDE.local.md`, no `.gitignore` |
| 5. Subprojeto | `backend/CLAUDE.md`, `scripts/migracao/CLAUDE.md`, `relatorios/CLAUDE.md` |

O documento traz a tabela pedida e também um mapa de "para onde foi cada parte do `/init`". Nenhuma regra aparece em dois níveis.

**Evidência:** o `/context` real ([`evidencias/ex03-context-inicial.md`](evidencias/ex03-context-inicial.md)) mostra que a sessão carrega `CLAUDE.md` (Project) e `CLAUDE.local.md` (Local). Os `CLAUDE.md` de subpastas não aparecem no início, o que confirma que são carregados sob demanda.

## Exercício 4: Context engineering

**Solução** ([`docs/ex04-context-engineering.md`](ex04-context-engineering.md)):

- O documento explica as **quatro estratégias** (Write, Select, Compress e Isolate) e os riscos de poisoning, confusion e clash.
- **Reprodução do risco.** Foi feita uma sessão real de 7 rodadas com uma premissa falsa na rodada 1. Os trechos reais mostram três coisas:
  - **poisoning:** a premissa foi gravada até na **auto-memória persistente**;
  - **clash:** a premissa contradizia a docstring do código, e o modelo percebeu;
  - **código errado:** o validador saiu com chaves fixas e o teste falhou (`FAILED (failures=1)`).
- **Mudança aplicada.** Foram três mudanças combinadas:
  - `/clear` entre tarefas;
  - `@arquivo` no lugar de "já combinamos";
  - a seção "Fonte da verdade" no `CLAUDE.md`.
- **Resultado da nova tentativa:** a mesma premissa foi **recusada na rodada 1**, nada foi gravado em memória e o validador saiu correto na primeira tentativa (`Ran 10 tests OK`). Esse validador foi incorporado ao projeto.

## Exercício 5: Sessões e `@arquivo`

**Solução:**

- Os dois arquivos de configuração foram criados com estruturas diferentes:
  - chaves com nomes diferentes;
  - um objeto aninhado (`janela`);
  - dias como siglas em um e como números no outro;
  - `pausas`, que só existe na tarde.
- Uma sessão real **nomeada** (`-n ex5-debug-sexta-tarde`) investigou um bug realista. A ordem foi:
  - `@horarios-manha.json`;
  - `/context`, para revisar o que estava ativo;
  - `@horarios-tarde.json`, com uma comparação chave a chave;
  - `@disponibilidade.py`, só para confirmar a convenção.
- Em seguida a sessão foi listada, retomada com `--resume` para revisão e encerrada.
- **Conclusão da sessão:** é um bug de configuração (falta o 5 em `dias_semana`). O diff foi proposto e **não foi aplicado**, por exigir aprovação humana.
- O documento ([`docs/ex05-sessoes-e-referencias.md`](ex05-sessoes-e-referencias.md)) mostra cada passo e explica por que a ordem evitou a confusão.

## Exercício 6: Plan mode

**Solução:**

- Uma sessão real com `--permission-mode plan` produziu o plano ([`evidencias/ex06-plano-plan-mode.md`](evidencias/ex06-plano-plan-mode.md)).
- Esse plano foi a base da spec versionada [`specs/cancelamento-reembolso.md`](../specs/cancelamento-reembolso.md), que cobre:
  - o comportamento esperado;
  - a regra de prazo;
  - 8 condições de borda;
  - a integração com os 3 módulos existentes;
  - 13 critérios de aceite.
- **Decisões justificadas** ([`docs/ex06-plan-mode.md`](ex06-plan-mode.md)):
  - **Cancelamento duplicado é idempotente.** O plano propunha erro. A spec mudou para idempotência porque um pedido duplicado costuma ser um retry de quem não sabe se a primeira chamada deu certo.
  - **Falha no gateway aborta o cancelamento.** O serviço não tem fila nem persistência para guardar um reembolso pendente com segurança.

## Exercício 7: `SPEC.md`

**Solução:**

- O [`SPEC.md`](../SPEC.md) tem **4 funcionalidades**: horários, pacientes, cancelamento e notificação.
- Cada funcionalidade tem objetivo, entradas, saídas, erros, critérios de aceite numerados e uma tabela "Código afetado" que aponta arquivo e símbolo e diz se aquele código é implementado, alterado, adicionado ou consumido.
- A seção §5 traz **4 riscos de divergência**, com o procedimento de reconciliação de cada um.

## Exercício 8: `AGENT.md`, `TASK.md`, `TOOLS.md`

**Solução:**

| Arquivo | Conteúdo |
|---|---|
| [`AGENT.md`](../AGENT.md) | Papel, limites e quando parar |
| [`TASK.md`](../TASK.md) | Passos, cada um com a seção da spec que cumpre, e a definição de pronto |
| [`TOOLS.md`](../TOOLS.md) | Ferramentas, ligadas ao `settings.json`, e módulos com o nível de acesso |

- Os três referenciam `SPEC.md §3.3` e `specs/…§n` sem copiar as regras.
- A justificativa da separação está em [`docs/ex07-ex08-artefatos.md`](ex07-ex08-artefatos.md). Cada arquivo tem um ciclo de vida diferente:
  - o papel é reutilizável;
  - a tarefa é descartável;
  - as permissões são auditáveis.
- Arquivos separados também deixam os diffs mais precisos e permitem carregar seletivamente só o que cada sessão precisa (estratégia *Select*).

## Exercício 9: Fluxo integrado

**Solução** ([`docs/ex09-fluxo-spec-driven.md`](ex09-fluxo-spec-driven.md)):

- Um diagrama Mermaid mostra 6 etapas e 2 checkpoints, com quem consome cada artefato: o desenvolvedor humano, o Claude Code em plan mode e o agente executor.
- **Checkpoint 1:** a skill `/revisar-spec` foi **executada de verdade** duas vezes sobre a spec do cancelamento ([`evidencias/ex09-revisar-spec.md`](evidencias/ex09-revisar-spec.md)), e as duas deram *PRECISA DE AJUSTES*.
  - **Primeira rodada:** apontou uma afirmação falsa sobre o relatório de ocupação e uma permissão descrita no `TOOLS.md` que não existia no `settings.json`.
  - **Segunda rodada:** apontou o risco de estorno em dobro num retry em outra faixa de prazo.
  - **Resultado:** os achados viraram a spec v1.2, o `TOOLS.md` revisado e o `settings.json` mais restrito, **antes** de qualquer linha de implementação. É a demonstração prática de que o fluxo pega a divergência cedo.
- **Fora do escopo do F3:** a segunda rodada também encontrou duas divergências entre o código atual e o `SPEC.md`. São o F2-CA3 (`telefone=""` é aceito) e o F1-CA3 (`carregar_agenda` não chama `validar_turno`). Elas ficaram registradas como trabalho pendente das tarefas de F1 e F2.
- **Checkpoint 2:** testes por critério, mais o subagente `revisor-spec` com contexto isolado.
- A justificativa cita esses dois pontos específicos de checagem e a aplicação dos limites pelo `settings.json`.

---

## Mapa de arquivos da entrega

```
TP1-AC/
├── README.md · CLAUDE.md · CLAUDE.local.md · SPEC.md · AGENT.md · TASK.md · TOOLS.md
├── .claude/settings.json · .claude/skills/revisar-spec/SKILL.md · .claude/agents/revisor-spec.md
├── hierarquia/nivel1-managed-policy/CLAUDE.md · hierarquia/nivel2-usuario/CLAUDE.md
├── backend/CLAUDE.md · backend/agendamento/*.py · backend/tests/*.py
├── config/horarios-manha.json · config/horarios-tarde.json
├── scripts/migracao/CLAUDE.md · migrar_pacientes_legado.py · exemplo_legado.csv
├── relatorios/CLAUDE.md · relatorio_ocupacao.py
├── specs/cancelamento-reembolso.md
└── docs/
    ├── RELATORIO-TECNICO.md (este arquivo)
    ├── onboarding-claude-code.md                (Ex. 1)
    ├── ex02-analise-init.md · ex02/CLAUDE.init-gerado.md   (Ex. 2)
    ├── ex03-hierarquia.md                       (Ex. 3)
    ├── ex04-context-engineering.md              (Ex. 4)
    ├── ex05-sessoes-e-referencias.md            (Ex. 5)
    ├── ex06-plan-mode.md                        (Ex. 6)
    ├── ex07-ex08-artefatos.md                   (Ex. 7 e 8)
    ├── ex09-fluxo-spec-driven.md                (Ex. 9)
    └── evidencias/  (transcrições .md, logs .jsonl, diffs, saídas de teste, /context, plano, revisão)
```
