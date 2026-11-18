# Serviço de Agendamento de Consultas

Novo serviço de agendamento de consultas médicas (migração do legado), desenvolvido com spec-driven development apoiado pelo Claude Code.

## Rodar

```bash
python3 -m unittest discover -s backend/tests -t backend          # testes
python3 relatorios/relatorio_ocupacao.py                          # relatório de ocupação
python3 scripts/migracao/migrar_pacientes_legado.py scripts/migracao/exemplo_legado.csv   # migração (dry-run)
```

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| `backend/agendamento/` | Módulos do serviço: disponibilidade, pacientes, notificação, validação de config |
| `config/` | Turnos de atendimento (`horarios-manha.json`, `horarios-tarde.json`) |
| `scripts/migracao/`, `relatorios/` | Subprojetos de migração do legado e de relatórios internos |
| `CLAUDE.md`, `*/CLAUDE.md`, `CLAUDE.local.md`, `hierarquia/` | Hierarquia de instruções do Claude Code |
| `.claude/` | Permissões, a skill `revisar-spec` e o subagente `revisor-spec` |
| `SPEC.md`, `specs/` | Especificação do serviço e specs detalhadas |
| `AGENT.md`, `TASK.md`, `TOOLS.md` | Artefatos de execução da funcionalidade de cancelamento |
| `docs/` | Documentos dos exercícios, relatório técnico e evidências |
