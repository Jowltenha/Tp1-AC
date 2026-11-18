---
name: formato-turnos-config
description: "config/horarios-*.json têm DOIS formatos (manhã e tarde); o formato \"único\" informado pelo usuário estava errado"
metadata:
  node_type: memory
  type: project
  originSessionId: 98945e61-58ba-4ca0-9634-ca54f1b6e928
  modified: 2026-11-18T22:26:34.091Z
---

Os arquivos de turno em `config/` NÃO seguem um formato único (verificado em 2026-11-18):

- Manhã (`horarios-manha.json`): `turno`, `inicio`, `fim`, `duracao_consulta_min`, `dias`.
- Tarde (`horarios-tarde.json`): `turno`, `janela{abre,fecha}`, `duracao_minutos`, `dias_semana` (1 a 7), `pausas[{de,ate}]`.

`normalizar_turno` em `backend/agendamento/disponibilidade.py` converte os dois formatos em `Turno`; qualquer validador ou leitor deve passar por ele ou aceitar os dois.

**Why:** o usuário disse no início da sessão que todos os arquivos tinham as chaves do formato da manhã e pediu para não reler. Isso gerou um validador que reprovou o arquivo da tarde, que está correto.

**How to apply:** não assuma formato único ao ler ou validar `horarios-*.json`; confira `normalizar_turno`. Alterar `config/horarios-*.json` em uso exige aprovação humana explícita (CLAUDE.md do projeto).
