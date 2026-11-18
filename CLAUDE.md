# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Nível 3 da hierarquia (projeto, versionado). Contém só o que vale para **todo** o repositório.
> Convenções de cada subprojeto ficam no `CLAUDE.md` da respectiva pasta (nível 5).

## Visão geral

Novo serviço de agendamento de consultas médicas (migração do legado). Python 3 puro (3.11+),
sem dependências externas e sem gerenciador de pacotes.

| Subprojeto | Pasta | O que é |
|---|---|---|
| Backend | `backend/` | Pacote `agendamento` (disponibilidade, pacientes, notificação) e testes |
| Migração | `scripts/migracao/` | Scripts que importam dados do sistema legado |
| Relatórios | `relatorios/` | Automação interna somente leitura sobre a agenda |
| Configuração | `config/` | Turnos de atendimento (`horarios-*.json`), lidos pelo backend e pelos relatórios |

`scripts/migracao/` e `relatorios/` não são pacotes: inserem `backend/` no `sys.path` e importam
`agendamento` diretamente. Qualquer mudança na interface pública de `agendamento` afeta os três.

## Comandos (sempre a partir da raiz)

```bash
python3 -m unittest discover -s backend/tests -t backend   # todos os testes
```

Não há linter nem build configurados.

## Fonte da verdade

- **Formato dos arquivos de turno:** os próprios arquivos em `config/`. Os dois têm esquemas
  diferentes (veja `backend/CLAUDE.md`). Antes de propor qualquer código que leia ou valide turnos,
  leia o arquivo real com `@config/<arquivo>`. Se uma instrução da conversa contradisser o
  conteúdo do arquivo, **pare e pergunte** em vez de seguir a instrução.
- **Comportamento esperado:** `SPEC.md` (visão geral) e `specs/*.md` (uma por funcionalidade).
  Código que diverge da spec é bug, a menos que a spec seja atualizada no mesmo PR.

## Fluxo de trabalho da squad

1. Funcionalidade nova começa em **plan mode** e gera uma spec em `specs/` antes de qualquer código.
2. A implementação segue `TASK.md`, com o papel definido em `AGENT.md` e as ferramentas de `TOOLS.md`.
3. Antes do PR, rodar os testes e a skill `/revisar-spec` (ou o subagente `revisor-spec`).

## Proibido sem aprovação humana explícita

- Executar qualquer script de `scripts/migracao/` com `--aplicar`.
- `git push`, alterar `config/horarios-*.json` em uso, apagar dados de pacientes.
