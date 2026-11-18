# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Novo serviço de agendamento de consultas médicas (migração do legado). Python 3 puro, sem dependências externas e sem gerenciador de pacotes.

## Comandos

Todos executados a partir da raiz do repositório.

```bash
# Todos os testes (unittest; o top-level é backend/ para que `agendamento` seja importável)
python3 -m unittest discover -s backend/tests -t backend

# Um único teste
cd backend && python3 -m unittest tests.test_modulos.TestDisponibilidade.test_pausa_da_tarde_e_respeitada

# Migração de pacientes do legado (dry-run por padrão; --aplicar grava de fato)
python3 scripts/migracao/migrar_pacientes_legado.py scripts/migracao/exemplo_legado.csv

# Relatório semanal de ocupação (gera relatorios/saida/ocupacao.csv, ignorado pelo git)
python3 relatorios/relatorio_ocupacao.py
```

Não há linter nem build configurados.

## Arquitetura

- `backend/agendamento/` é o pacote central, com três módulos independentes entre si:
  - `disponibilidade.py` — gera slots livres por médico/data a partir de `config/horarios-*.json` e guarda reservas em memória (`reservar` / `liberar`).
  - `pacientes.py` — `RepositorioPacientes` em memória com validação de CPF/e-mail. A interface pública (`cadastrar`, `buscar_por_cpf`, `atualizar_contato`) deve ser preservada quando a persistência real for introduzida.
  - `notificacao.py` — `Notificador` monta mensagens a partir de `TEMPLATES` e entrega via um `Canal` (Protocol). `CanalConsole` é o único canal implementado e é usado nos testes.
- `scripts/migracao/` e `relatorios/` não são pacotes: inserem `backend/` no `sys.path` e importam `agendamento` diretamente.

## Armadilha: formatos dos arquivos de turno

Os dois arquivos de `config/` têm **esquemas diferentes**, e `normalizar_turno` decide o formato pela presença da chave `janela`:

| Arquivo | Horário | Duração | Dias | Pausas |
|---|---|---|---|---|
| `horarios-manha.json` | `inicio` / `fim` | `duracao_consulta_min` | `dias` (siglas `"seg"`…) | — |
| `horarios-tarde.json` | `janela.abre` / `janela.fecha` | `duracao_minutos` | `dias_semana` (1 = seg) | `pausas[{de, ate}]` |

Ao alterar ou adicionar um arquivo de turno, leia o arquivo real e ajuste `normalizar_turno` — não presuma o formato a partir do outro arquivo.
