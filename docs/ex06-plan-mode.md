# Exercício 6: Plan mode e a spec de cancelamento com reembolso

## Como foi feito

1. **Planejamento em plan mode.** A sessão `870d4f97` foi executada com `claude -p "<pedido>" --permission-mode plan`. Na interface interativa, o equivalente é `Shift+Tab` duas vezes ou `/plan`. Em plan mode o Claude Code só pode ler e pesquisar: o log mostra 12 turnos e nenhuma edição de código. Antes de planejar, ele leu os módulos de `backend/agendamento/`, os `CLAUDE.md` e o `CLAUDE.local.md`.
2. **Plano gerado.** O plano foi gravado pelo próprio Claude Code em `~/.claude/plans/…` e copiado para o repositório em [`evidencias/ex06-plano-plan-mode.md`](evidencias/ex06-plano-plan-mode.md). Esse plano notou sozinho que **não existe a entidade "consulta"** no código atual (`reservados` guarda só `(medico_id, datetime)`). Notou também que `specs/` não existia, embora o `CLAUDE.local.md` citasse `specs/cancelamento-reembolso.md`. Ao final, listou cinco premissas para confirmação humana.
3. **Spec versionada.** O plano revisado virou [`specs/cancelamento-reembolso.md`](../specs/cancelamento-reembolso.md), um arquivo Markdown commitado no git e não apenas um texto de conversa. As premissas foram decididas e a spec ganhou critérios de aceite numerados e o identificador `SPEC-F3`, referenciado no `SPEC.md`. Depois passou por duas rodadas do checkpoint 1 (`/revisar-spec`, veja o Ex. 9) e chegou à v1.2, com 13 critérios.

## O que a spec cobre

| Exigência do exercício | Seção da spec |
|---|---|
| Comportamento esperado | §3, o fluxo de 8 passos de `ServicoCancelamento.cancelar` |
| Regra de prazo | §4, a tabela 100% / 50% / 0% com limites fechados à esquerda |
| Condições de borda, incluindo cancelamento fora do prazo | §5, casos B1 a B8 |
| Pontos de integração com os módulos existentes | §6, `disponibilidade.liberar`, `pacientes.buscar_por_id` e os novos templates de `notificacao` |
| Critérios de aceite testáveis | §7, CA1 a CA13 |

## O que mudou entre o plano e a spec

| Premissa do plano | Decisão na spec |
|---|---|
| Cancelamento duplicado levanta `ValueError` | **Mudou:** o cancelamento passa a ser idempotente e devolve o mesmo resultado (B2) |
| Falha no gateway aborta o cancelamento | Mantida (B5) |
| Exatamente 2h conta como 50% | Mantida (§4) |
| Cancelar com menos de 2h é permitido, sem reembolso | Mantida (B1) |
| Valores em centavos, arredondados para baixo | Mantida (§4, CA4) |
| *(não existia no plano)* | **Adicionado:** B8, dois cancelamentos concorrentes |
| Chave de idempotência = `consulta_id`, com o valor recalculado a cada tentativa | **Refinada no checkpoint 1:** o valor da primeira tentativa fica gravado (`reembolso_pendente_centavos`) e é reutilizado no retry (B5, CA13) |

## Justificativa de duas decisões

**Decisão 1: cancelamento duplicado é idempotente (B2) e não um erro.** O plan mode propôs que a segunda chamada a `cancelar` levantasse `ValueError("Consulta já cancelada")`. A spec mudou isso para devolver o mesmo `ResultadoCancelamento` da primeira vez, sem chamar o gateway e sem notificar de novo. O motivo é a forma como um cancelamento chega duplicado na prática. Quase sempre é um *retry*: o paciente clica duas vezes, o app reenvia depois de um timeout de rede, ou a recepção tenta de novo porque a tela não atualizou. Em todos esses casos o cliente **não sabe** se a primeira chamada deu certo. Se a resposta for um erro, a mensagem que ele recebe ("já cancelada") é ambígua e pode ser lida como falha, o que leva a ligações para o suporte e pedidos de estorno manual. Com uma resposta idempotente, o pedido repetido recebe o mesmo resultado do primeiro, com o valor e a referência do estorno. A garantia que importa para o dinheiro continua igual nos dois desenhos: **o gateway é chamado no máximo uma vez** (CA5). Isso é reforçado pela chave de idempotência `consulta_id` enviada ao gateway e pelo lock por consulta (B8).

**Decisão 2: falha no gateway aborta o cancelamento inteiro (B5).** A alternativa seria cancelar a consulta, liberar o slot e deixar o reembolso "pendente" numa fila para processar depois. Ela foi rejeitada porque cria um estado que o serviço atual não tem como gerenciar. Não há fila, worker nem persistência, então um reembolso pendente simplesmente se perderia. Além disso, o slot liberado poderia ser reservado por outro paciente enquanto o primeiro ainda não recebeu o dinheiro, e não haveria como voltar atrás sem prejudicar alguém. Abortando, o sistema fica sempre em um de dois estados consistentes: "agendada e paga" ou "cancelada, com o reembolso feito". Repetir é seguro. O valor calculado na primeira tentativa fica gravado na consulta, e o retry usa **o mesmo valor e a mesma chave** (`consulta_id`). Se a primeira tentativa chegou a estornar antes do timeout, o gateway reconhece a chave e não estorna de novo, mesmo que o retry aconteça depois de a consulta ter mudado de faixa de prazo. Esse refinamento veio da segunda rodada do `/revisar-spec` (Ex. 9). Por isso a ordem do fluxo em §3 é **estornar → marcar → liberar → notificar**: tudo o que vem depois do estorno é local e não falha por motivo externo, e a notificação (o único passo externo depois do estorno) é de melhor esforço (B6). Quando o serviço tiver persistência e fila, a decisão pode ser revista em uma nova versão da spec.
