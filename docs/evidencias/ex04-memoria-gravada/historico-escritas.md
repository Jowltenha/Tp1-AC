# Escritas na auto-memória feitas pela sessão 98945e61 (extraídas do transcript .jsonl)

## 2026-11-18T22:25:06.353Z · Write `project_formato_turnos_config.md`

```markdown
---
name: formato-turnos-config
description: Formato padrão dos arquivos de turno em config/horarios-*.json (chaves obrigatórias)
metadata:
  type: project
---

Todos os arquivos de turno em `config/` seguem o mesmo formato, com as chaves `inicio`, `fim`, `duracao_consulta_min` e `dias` (informado pelo usuário, não verificado nos arquivos).

**Why:** o usuário pediu para guardar isso como convenção da squad; backend e relatórios leem esses arquivos.

**How to apply:** ao criar, validar ou ler um `horarios-*.json`, assuma essas quatro chaves. Lembre que alterar `config/horarios-*.json` em uso exige aprovação humana explícita (CLAUDE.md do projeto).
```

## 2026-11-18T22:25:07.040Z · Write `MEMORY.md`

```markdown
- [Formato dos turnos em config/](project_formato_turnos_config.md) — horarios-*.json têm as chaves inicio, fim, duracao_consulta_min, dias
```

## 2026-11-18T22:26:34.085Z · Write `project_formato_turnos_config.md`

```markdown
---
name: formato-turnos-config
description: config/horarios-*.json têm DOIS formatos (manhã e tarde); o formato "único" informado pelo usuário estava errado
metadata:
  type: project
---

Os arquivos de turno em `config/` NÃO seguem um formato único (verificado em 2026-11-18):

- Manhã (`horarios-manha.json`): `turno`, `inicio`, `fim`, `duracao_consulta_min`, `dias`.
- Tarde (`horarios-tarde.json`): `turno`, `janela{abre,fecha}`, `duracao_minutos`, `dias_semana` (1 a 7), `pausas[{de,ate}]`.

`normalizar_turno` em `backend/agendamento/disponibilidade.py` converte os dois formatos em `Turno`; qualquer validador ou leitor deve passar por ele ou aceitar os dois.

**Why:** o usuário disse no início da sessão que todos os arquivos tinham as chaves do formato da manhã e pediu para não reler. Isso gerou um validador que reprovou o arquivo da tarde, que está correto.

**How to apply:** não assuma formato único ao ler ou validar `horarios-*.json`; confira `normalizar_turno`. Alterar `config/horarios-*.json` em uso exige aprovação humana explícita (CLAUDE.md do projeto).
```

## 2026-11-18T22:26:34.801Z · Write `MEMORY.md`

```markdown
- [Formatos dos turnos em config/](project_formato_turnos_config.md) — horarios-*.json têm 2 formatos (manhã e tarde); usar normalizar_turno
```

