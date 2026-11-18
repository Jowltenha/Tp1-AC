# Exercício 5: Gestão de sessões e referências `@arquivo`

## Cenário

A recepção relatou: *"na sexta-feira 20/11/2026 não aparece nenhum horário à tarde"*. O projeto tem dois arquivos de turno com **estruturas diferentes**:

| | [`config/horarios-manha.json`](../config/horarios-manha.json) | [`config/horarios-tarde.json`](../config/horarios-tarde.json) |
|---|---|---|
| Horário | `inicio` / `fim` (no nível de cima) | `janela.abre` / `janela.fecha` (objeto aninhado) |
| Duração | `duracao_consulta_min` | `duracao_minutos` |
| Dias | `dias`: siglas `["seg", …, "sex"]` | `dias_semana`: números `[1, 2, 3, 4]` |
| Pausas | não tem | `pausas: [{de, ate}]` |

O colega da squad perdeu tempo porque o Claude Code **supôs** o formato da tarde a partir do da manhã, ou porque nenhum dos dois arquivos estava no contexto. A sessão abaixo foi conduzida para evitar exatamente isso.

## Sessão real

- `session_id 4f0a41a4`, com o nome `ex5-debug-sexta-tarde`.
- Transcrição completa: [`evidencias/ex05-sessao.md`](evidencias/ex05-sessao.md)
- Log bruto: [`evidencias/ex05-transcript.jsonl`](evidencias/ex05-transcript.jsonl)
- Lista de sessões: [`evidencias/ex05-lista-sessoes.md`](evidencias/ex05-lista-sessoes.md)

### Passo a passo

| # | Comando / referência | O que aconteceu | Por que nesta ordem |
|---|---|---|---|
| 0 | **`/clear`** (ou sessão nova) com nome: `claude -n ex5-debug-sexta-tarde` | A sessão começou com o contexto limpo, só com os `CLAUDE.md` | Para não herdar nada de sessões anteriores, como o validador do Exercício 4. O nome permite achar a sessão depois em `/resume` |
| 1 | **`@config/horarios-manha.json`**, com a ordem de "não abra outro config" | O Claude Code leu **só** esse arquivo: *"segunda a sexta (…) das 08:00 às 12:00, consultas de 30 minutos. Não abri nenhum outro arquivo de config."* | Primeiro fixa o que funciona (a manhã de sexta aparece) e cria uma linha de base sem misturar os formatos |
| 2 | **`/context`** | 60k/200k tokens, dos quais 22,3k de mensagens. Em *Memory files* aparece só o `CLAUDE.md` do projeto | **Revisar** o que está ativo antes de trazer o segundo arquivo: confirma que não há resto de outra tarefa |
| 3 | **`@config/horarios-tarde.json`**, com o pedido de comparar chave a chave | Montou a tabela com as 6 chaves e os tipos. Achou `dias_semana: [1,2,3,4]`, sem o 5. Também **não afirmou a convenção** sem prova: *"`[1,2,3,4]` só significa seg–qui se 1 for segunda (…) eu não confirmei no código."* | O segundo arquivo entra **só depois** do primeiro estar entendido, e o pedido de comparação obriga a olhar o conteúdo real de cada um |
| 4 | **`@backend/agendamento/disponibilidade.py`** | Confirmou em `normalizar_turno` (linha 82) que `DIAS_SEMANA[n - 1]` faz 1 = seg. A conclusão foi **bug de configuração**, e ele propôs o diff `[1,2,3,4]` → `[1,2,3,4,5]` **sem aplicar**, porque é preciso aprovação humana | O código entra por último, só para tirar a única dúvida que os dados não resolviam |
| 5 | **Listar sessões**: `/resume` (interativo) ou `claude --resume` sem id | Mostrou as sessões do projeto com nome, data e primeiro prompt ([`ex05-lista-sessoes.md`](evidencias/ex05-lista-sessoes.md)) | Para achar a sessão de depuração entre outras: as duas do Ex. 4, a de plan mode e a principal |
| 6 | **Retomar e revisar**: `claude --resume 4f0a41a4…` (o mesmo que escolher no `/resume`) | Resumiu a investigação etapa por etapa e o que falta: *"aprovar a mudança de `dias_semana` para `[1, 2, 3, 4, 5]` (…) Antes, confirmar no `SPEC.md`"* | Volta ao estado exato sem reexplicar nada, e confirma que o contexto da sessão continua coerente |
| 7 | **Encerrar**: `/clear` (ou `/exit`) depois de registrar a decisão pendente | A sessão foi encerrada. O que importa ficou **fora** dela: o diff proposto está neste documento e a pendência foi para o tech lead | Para que a próxima tarefa (Ex. 6, plan mode do cancelamento) não comece com os dois JSON e a discussão do bug na janela |

## Por que a ordem evitou a confusão

1. **Um arquivo de cada vez, cada um nomeado com `@`.** No passo 1 a janela tinha só o formato da manhã. No passo 3 o da tarde entrou junto com o pedido explícito de comparação. O modelo nunca teve que "adivinhar" qual arquivo tinha qual chave. Os dois conteúdos estavam na janela, um ao lado do outro, e com nomes diferentes. O colega teve o problema oposto: um arquivo ausente e o outro usado como modelo.
2. **`@` em vez de descrever.** O `@arquivo` coloca o **conteúdo real** na conversa. Escrever "o arquivo da tarde tem as mesmas chaves" teria repetido o envenenamento do Exercício 4.
3. **`/context` antes do segundo arquivo** confirmou que a janela estava limpa (só `CLAUDE.md` e a etapa 1), então nenhuma suposição antiga podia entrar em conflito.
4. **Dados antes do código.** Quem decide o bug são os dados (`dias_semana` não tem o 5). O código entrou só para confirmar a convenção 1 = seg. Se o código tivesse entrado primeiro, o modelo poderia ter "corrigido" `normalizar_turno` para encaixar uma hipótese, que é exatamente o tipo de correção baseada em suposição errada que o colega recebeu.
5. **Sessão nomeada e encerrada.** O nome permitiu retomar e revisar a sessão certa. Encerrar com `/clear` impediu que os dois formatos de JSON passassem para a tarefa seguinte.

## Resultado

- **Causa:** `config/horarios-tarde.json` não tem o 5 (sexta) em `dias_semana`. O código está correto.
- **Correção proposta, aguardando aprovação humana:**
  ```diff
  -  "dias_semana": [1, 2, 3, 4],
  +  "dias_semana": [1, 2, 3, 4, 5],
  ```
- **Não foi aplicada**, de acordo com a regra do `CLAUDE.md` ("alterar `config/horarios-*.json` em uso exige aprovação humana"). Também não está claro se a clínica atende sexta à tarde. Isso ficou registrado como dúvida de negócio no [`SPEC.md`](../SPEC.md), seção 3.1.
