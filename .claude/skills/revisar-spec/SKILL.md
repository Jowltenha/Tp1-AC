---
name: revisar-spec
description: Revisa um artefato de especificação (SPEC.md, specs/*.md, TASK.md) do serviço de agendamento contra o código existente e aponta lacunas, ambiguidades e divergências. Use quando alguém pedir para revisar, validar ou checar uma especificação.
---

# Revisar especificação

Você está revisando uma especificação do serviço de agendamento de consultas.

1. Leia o arquivo de especificação indicado pelo usuário por completo.
2. Para cada funcionalidade, localize no código (`backend/agendamento/`, `config/`, `scripts/`, `relatorios/`) as funções e arquivos que ela cita. Use busca, não suposição.
3. Produza uma tabela com as colunas: **Seção da spec | Problema | Tipo | Evidência (arquivo:linha) | Sugestão**.
   - Tipos válidos: `ambiguidade`, `lacuna`, `divergência com o código`, `critério de aceite não testável`.
4. Termine com um veredito: `PRONTA PARA IMPLEMENTAÇÃO` ou `PRECISA DE AJUSTES`, com no máximo três frases de justificativa.

Regras:
- Não edite a especificação nem o código; apenas reporte.
- Toda divergência com o código precisa citar `arquivo:linha` real.
