# backend/ — convenções do subprojeto

> Nível 5 (subdiretório). Carregado quando o Claude Code trabalha com arquivos de `backend/`.

## Testes

- Framework: `unittest` da biblioteca padrão (não instalar pytest).
- Um teste isolado: `cd backend && python3 -m unittest tests.test_modulos.TestDisponibilidade.test_pausa_da_tarde_e_respeitada`
- Testes de disponibilidade usam datas fixas de novembro/2026 (16/11 = segunda, 20/11 = sexta).
  Não use `date.today()` em testes.

## Formatos dos arquivos de turno

`normalizar_turno` em `agendamento/disponibilidade.py` decide o formato pela presença da chave `janela`:

| Arquivo | Horário | Duração | Dias | Pausas |
|---|---|---|---|---|
| `horarios-manha.json` | `inicio` / `fim` | `duracao_consulta_min` | `dias` (siglas `"seg"`…) | — |
| `horarios-tarde.json` | `janela.abre` / `janela.fecha` | `duracao_minutos` | `dias_semana` (1 = seg) | `pausas[{de, ate}]` |

Todo o resto do código usa apenas o `Turno` normalizado; nunca leia as chaves cruas do JSON fora de `normalizar_turno`.

## Convenções de código

- Identificadores e mensagens em português, sem acentos em nomes de variáveis/funções.
- Erros de regra de negócio são `ValueError` com mensagem legível; "não encontrado" é `KeyError`.
- Repositórios são em memória por enquanto. Preserve a interface pública (`cadastrar`,
  `buscar_por_cpf`, `atualizar_contato`, `reservar`, `liberar`) porque `scripts/` e `relatorios/` dependem dela.
- `notificacao.py`: novos tipos de mensagem entram em `TEMPLATES`; nos testes use `CanalConsole`.
