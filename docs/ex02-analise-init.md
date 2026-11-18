# Exercício 2: análise do CLAUDE.md gerado pelo `/init`

## Como foi feito

1. Foram criados três módulos do serviço em `backend/agendamento/`, mais testes, configs e os dois subprojetos auxiliares:
   - `disponibilidade.py`: gera os slots de consulta a partir de `config/horarios-*.json` e controla as reservas.
   - `pacientes.py`: cadastro de pacientes com validação de CPF e e-mail.
   - `notificacao.py`: mensagens por template, entregues por um `Canal`.
   - `backend/tests/test_modulos.py` (7 testes, `unittest`), `scripts/migracao/migrar_pacientes_legado.py` e `relatorios/relatorio_ocupacao.py`.
2. O commit `a9856ba` registrou essa estrutura.
3. O comando `/init` foi executado dentro do Claude Code, na raiz do projeto. O arquivo que ele gerou foi guardado sem nenhuma alteração em [`docs/ex02/CLAUDE.init-gerado.md`](ex02/CLAUDE.init-gerado.md), que também está no commit `5406a8e`.

## O que o `/init` capturou corretamente

| Item | Por que está certo |
|---|---|
| Comando de testes `python3 -m unittest discover -s backend/tests -t backend` | É o comando que de fato funciona. O `-t backend` é necessário, e ele explicou o motivo (deixar `agendamento` importável). |
| Como rodar **um único teste** | O `cd backend && python3 -m unittest tests.test_modulos...` é um caminho que não aparece em nenhum arquivo. Ele foi deduzido da estrutura dos pacotes. |
| "Não há linter nem build" | É verdade e evita que outra sessão tente rodar `npm`, `make` ou `pytest`. |
| `scripts/` e `relatorios/` alteram o `sys.path` | Para saber isso é preciso ler três arquivos diferentes. É o tipo de informação de "visão geral" que o `/init` deve capturar. |
| A interface pública de `RepositorioPacientes` precisa ser preservada | Saiu da docstring de `pacientes.py`, e ele relacionou essa interface com quem a consome. |
| Tabela dos **dois formatos de turno** | Foi a parte mais útil: ele comparou os dois JSON chave por chave e registrou a regra de detecção (presença de `janela`). |

## O que ficou genérico ou incompleto

| Lacuna | Consequência |
|---|---|
| Tudo ficou em **um arquivo só** na raiz, misturando backend, migração e relatórios | Uma sessão que só mexe em relatórios carrega regras de migração que não precisa. Quando o projeto crescer, o arquivo raiz vai inchar. |
| **Nenhuma regra de segurança.** Ele documentou `--aplicar` como "grava de fato", mas não disse que é proibido rodar sem um humano | Uma sessão pode executar a migração real seguindo o próprio CLAUDE.md. |
| **Não registra o fluxo da squad** (plan mode, specs em `specs/`, `SPEC.md` como fonte da verdade) | O `/init` só enxerga código. Processo não fica no código, então ele não tinha como saber. |
| **Não diz quem é a fonte da verdade** quando a conversa contradiz um arquivo | É justamente o risco que apareceu no Exercício 4: uma instrução errada na conversa substituiu o conteúdo real do arquivo. |
| Convenções de cada subprojeto (CSV `latin-1` com `;`, dry-run, relatórios somente leitura, datas fixas nos testes) | Ele leu o código mas não transformou esses detalhes em regras. Ficaram implícitos. |
| Sem versão mínima do Python e sem informação do ambiente (WSL, só existe `python3`) | São informações pessoais ou de ambiente, que não deveriam ir no arquivo versionado. Mesmo assim precisam ficar em algum lugar. |

## Ajustes manuais antes de liberar para a squad

1. **Separar por escopo** (aplicado no Exercício 3): o arquivo raiz fica só com a visão geral e as regras globais. A tabela de formatos e as convenções de teste vão para `backend/CLAUDE.md`, e as regras de CSV e dry-run vão para `scripts/migracao/CLAUDE.md`.
2. **Adicionar a seção "Proibido sem aprovação humana"** (`--aplicar`, `git push`, editar turnos em uso) e reforçar cada item com `permissions.deny` em `.claude/settings.json`. Instrução escrita sozinha não é suficiente.
3. **Adicionar a seção "Fonte da verdade"**: o formato dos turnos é o que está nos arquivos de `config/`, e o comportamento esperado é o que está no `SPEC.md`. Se a conversa contradisser um arquivo, a sessão deve parar e perguntar.
4. **Registrar o fluxo spec-driven** (plan mode, depois `specs/`, depois `TASK.md`, depois `/revisar-spec`), que o `/init` não tinha como deduzir.
5. **Levar informações pessoais e de ambiente para `CLAUDE.local.md`** (fora do git), em vez de colocá-las no arquivo compartilhado.

## Conclusão

O `/init` funcionou bem para os **fatos que estão no código**: comandos, estrutura, dependências entre pastas e formatos de dados. Ele ficou fraco no que está **fora do código**, como as regras de segurança, o processo da squad, a separação por escopo e o que fazer quando há conflito de informação. Por isso o arquivo gerado é um bom ponto de partida, mas precisa da revisão de alguém da squad antes de virar a referência do time.
