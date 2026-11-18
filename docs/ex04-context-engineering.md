# Exercício 4: Context engineering no Claude Code

**Público:** desenvolvedores júnior da squad de agendamento.
**Motivo da sessão:** dois colegas tiveram respostas inconsistentes depois de sessões longas de refatoração.

## 1. A janela de contexto

A cada resposta, o modelo só "enxerga" o que está na **janela de contexto**: o prompt de sistema, as definições de ferramentas, os arquivos `CLAUDE.md` carregados, as mensagens da conversa e os resultados de ferramentas (cada arquivo lido, cada saída de teste). A janela tem tamanho fixo (200k tokens nesta configuração, confirmado com `/context`) e tudo dentro dela compete pela atenção do modelo. Uma frase errada dita no começo da sessão continua lá, com o mesmo peso de um arquivo lido agora.

A medição real no início de uma sessão deste projeto ([`evidencias/ex03-context-inicial.md`](evidencias/ex03-context-inicial.md)) deu ~36k tokens antes de qualquer mensagem. Desse total, 583 tokens são do `CLAUDE.md` do projeto e 123 do `CLAUDE.local.md`. Depois de três rodadas de investigação (Exercício 5) já eram **60k tokens**, e 22k deles eram de mensagens.

## 2. As quatro estratégias

| Estratégia | O que é | Como fazer no Claude Code | Efeito na qualidade |
|---|---|---|---|
| **1. Write (gravar fora da janela)** | Tirar a informação da conversa e guardar em um lugar persistente, para ela voltar só quando for útil | `CLAUDE.md` em camadas, auto-memória (`~/.claude/projects/.../memory/`), specs e planos em arquivos `.md` versionados, `TASK.md` | A conversa pode ser limpa sem perder decisões. O que foi gravado sobrevive a `/clear` e a novas sessões. **Risco:** gravar algo errado faz o erro durar mais que a sessão (foi o que aconteceu no experimento abaixo) |
| **2. Select (selecionar o que entra)** | Trazer para a janela **só** o que a tarefa precisa, na hora em que precisa | `@arquivo` no prompt, `CLAUDE.md` de subpasta (carregado sob demanda), skills (só a descrição fica sempre carregada e o corpo entra quando é usada), Grep/Glob antes de Read | Menos ruído e mais atenção para o que importa. O modelo trabalha com o conteúdo real, não com suposições |
| **3. Compress (comprimir)** | Trocar um histórico longo por um resumo | `/compact [instruções do que manter]`. A auto-compactação dispara sozinha perto do limite (o "Autocompact buffer" de 33k que aparece no `/context`) | Libera espaço sem começar do zero. **Risco:** o resumo pode deixar de fora um detalhe ou preservar uma premissa errada |
| **4. Isolate (isolar)** | Separar o trabalho em contextos independentes | `/clear` entre tarefas, uma sessão por assunto (`-n nome`, `/resume`), **subagentes** (cada um com janela própria e devolvendo só o resumo), worktrees | Uma tarefa não contamina a outra. O revisor (`revisor-spec`) não herda as premissas de quem escreveu o código |

### Riscos de contexto

- **Poisoning (envenenamento):** uma informação errada entra no contexto (uma alucinação, uma premissa falsa do usuário, um arquivo desatualizado) e passa a ser tratada como verdade nas respostas seguintes.
- **Distraction / Confusion (confusão):** há tanta informação irrelevante ou parecida que o modelo usa a errada. Por exemplo, aplica o formato de um arquivo de config ao outro (o caso do Exercício 5).
- **Clash (conflito):** duas informações no contexto se contradizem (a conversa diz uma coisa e o arquivo, ou o `CLAUDE.md`, diz outra), e a resposta oscila entre as duas.

## 3. Experimento: reprodução do risco

### Como foi feito

Foi feita uma sessão **real** do Claude Code 2.1.281 com 7 rodadas no mesmo `session_id` (`98945e61`), usando `claude -p … --resume <id>` em sequência. O script está em [`evidencias/rodar_sessao.sh`](evidencias/rodar_sessao.sh) e os prompts em [`evidencias/prompts-ex4-antes.txt`](evidencias/prompts-ex4-antes.txt). A sessão rodou numa cópia do projeto (git worktree) em que o `CLAUDE.md` **não tinha** a seção "Fonte da verdade" nem a tabela de formatos, como era o arquivo antes da reorganização.

Na rodada 1 foi colocada de propósito uma **premissa falsa**: "todos os arquivos de turno seguem o formato `inicio/fim/duracao_consulta_min/dias`". Na verdade só o da manhã segue esse formato. Depois vieram 4 rodadas de refatorações sem relação com isso, e só na rodada 6 foi pedido um validador de turnos.

Arquivos de evidência:

- Transcrição: [`evidencias/ex04-sessao-antes.md`](evidencias/ex04-sessao-antes.md)
- Log bruto `.jsonl`: [`evidencias/ex04-transcript-antes.jsonl`](evidencias/ex04-transcript-antes.jsonl)
- Diff produzido: [`evidencias/ex04-diff-antes.patch`](evidencias/ex04-diff-antes.patch)
- Resultado dos testes: [`evidencias/ex04-testes-antes.txt`](evidencias/ex04-testes-antes.txt)
- Memória gravada: [`evidencias/ex04-memoria-gravada/`](evidencias/ex04-memoria-gravada/)

### Como o risco apareceu (trechos reais)

**1. Poisoning: a premissa falsa entrou e foi gravada na memória persistente** (rodada 1). A primeira versão da memória foi gravada às 22:25:06Z. O log mostra a chamada `Write` em `project_formato_turnos_config.md`:

> "Todos os arquivos de turno em `config/` seguem o mesmo formato, com as chaves `inicio`, `fim`, `duracao_consulta_min` e `dias` (informado pelo usuário, não verificado nos arquivos). … **How to apply:** ao criar, validar ou ler um `horarios-*.json`, assuma essas quatro chaves."

Na resposta, o próprio Claude Code avisou: *"Anotei que isso veio de você e que não conferi nos arquivos de `config/`."* Mesmo assim, a regra "assuma essas quatro chaves" ficou gravada.

**2. Clash: o contexto passou a ter duas verdades** (rodada 5, numa pergunta sem relação, sobre `reservar`/`liberar`):

> "Em `disponibilidade.py:77`, a docstring de `normalizar_turno` diz que existem 'dois formatos de arquivo de turno'. Isso contradiz o que você me disse, que todos os arquivos de `config/` seguem o mesmo formato."

**3. O código foi gerado a partir da premissa envenenada** (rodada 6). Mesmo com o conflito já percebido, o modelo seguiu a instrução da conversa ("sem reler… já combinamos o formato"):

```python
CHAVES_OBRIGATORIAS = ("inicio", "fim", "duracao_consulta_min", "dias")
```

O teste real falhou ([`ex04-testes-antes.txt`](evidencias/ex04-testes-antes.txt)):

```
- ['Chave obrigatória ausente: inicio',
-  'Chave obrigatória ausente: fim',
-  'Chave obrigatória ausente: duracao_consulta_min',
-  'Chave obrigatória ausente: dias']
Ran 15 tests ... FAILED (failures=1)
```

**4. Reconhecimento na rodada 7:**

> "**A culpa é do validador, não do arquivo de configuração.** … a premissa do formato único estava errada, e eu a aceitei sem conferir."

**Diagnóstico:**

- Houve **poisoning**: uma premissa falsa entrou na conversa e na memória persistente.
- Isso levou a um **clash**: a premissa contradizia a docstring do código.
- O efeito foi código errado. A sessão gastou 34 mensagens e 7 rodadas para chegar a um validador que **não funciona**.
- O dano maior foi a premissa gravada em memória. Sem correção, ela seria carregada em **toda sessão futura** do projeto. Na rodada 7 o próprio Claude corrigiu a memória, e o autor do TP também apagou o arquivo, porque era só do experimento.

## 4. Mudanças aplicadas

Foram três mudanças. Cada uma ataca uma causa diferente:

| # | Mudança | Estratégia | Onde |
|---|---|---|---|
| 1 | **`/clear` ao trocar de tarefa.** A refatoração de `pacientes.py` e o validador de turnos ficaram em sessões separadas | Isolate | Condução da sessão |
| 2 | **Reformular a instrução** com `@config/horarios-manha.json` e `@config/horarios-tarde.json` em vez de "já combinamos o formato" | Select | Prompt |
| 3 | **Reorganizar o `CLAUDE.md`** com a seção "Fonte da verdade": o formato é o que está nos arquivos, e se a conversa contradisser um arquivo, a sessão **para e pergunta**. A tabela de formatos fica em `backend/CLAUDE.md` | Write | [`CLAUDE.md`](../CLAUDE.md), [`backend/CLAUDE.md`](../backend/CLAUDE.md) |

### Resultado da nova tentativa (sessões reais `0863d4d2` e `8a3ea186`)

Os prompts estão em [`evidencias/prompts-ex4-depois.txt`](evidencias/prompts-ex4-depois.txt) e a transcrição em [`evidencias/ex04-sessao-depois.md`](evidencias/ex04-sessao-depois.md). A **mesma premissa falsa** foi repetida na rodada 1.

**A premissa foi recusada na hora** (rodada 1), por causa da mudança 3:

> "**Os arquivos de turno não seguem todos o mesmo formato, ao contrário do que você disse.** Só `config/horarios-manha.json` usa as chaves que você citou … Pelas regras do projeto, não vou guardar a premissa de formato único."

Nenhum arquivo de memória foi gravado. O diretório `memory/` continuou vazio.

Depois do **`/clear`** (que gerou o novo `session_id` `8a3ea186`), a tarefa do validador chegou com os `@arquivos` e o resultado foi:

> "A função escolhe o formato como `normalizar_turno` faz, pela presença de `janela`. … Os dois arquivos reais batem com o que a instrução dizia, então não houve conflito a resolver."

```
Ran 10 tests in 0.004s
OK
```

| Métrica | Antes | Depois |
|---|---|---|
| Premissa falsa aceita | Sim, e gravada em memória | Não, recusada na rodada 1 |
| Validador correto na primeira tentativa | Não (15 testes, 1 falha) | Sim (10 testes, 0 falhas) |
| Rodadas até ter um validador funcionando | Não chegou lá em 7 | 1 rodada depois do `/clear` |

O validador da segunda tentativa foi incorporado ao projeto em [`backend/agendamento/validacao_config.py`](../backend/agendamento/validacao_config.py).

## 5. Regras para o time

1. **Uma tarefa, uma sessão.** Use `/clear` ao trocar de assunto. Para voltar a um assunto, use `/resume`.
2. **Mostre, não descreva.** Use `@arquivo` em vez de "o formato é X".
3. **Nunca diga "não precisa reler".** Isso desliga a checagem que protege contra o envenenamento.
4. **Use `/context`** quando a sessão parecer estranha: veja quantos tokens são de mensagens antigas.
5. **Revise a auto-memória** (`/memory`) depois de sessões longas. Uma premissa errada gravada ali vira um envenenamento permanente.
6. **Use `/compact` com instruções** (por exemplo, "mantenha só as decisões e os arquivos alterados") quando precisar continuar a mesma tarefa com a janela cheia.
