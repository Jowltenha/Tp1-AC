# Exercício 3: hierarquia de arquivos de instrução

O CLAUDE.md que o `/init` gerou no Exercício 2 foi dividido em cinco níveis. O Claude Code carrega todos os níveis que se aplicam e os combina. Os níveis mais específicos completam os mais gerais, e a política gerenciada (nível 1) não pode ser sobrescrita. Os arquivos acima do diretório de trabalho são carregados quando a sessão começa. Os `CLAUDE.md` de subpastas são carregados **sob demanda**, quando o Claude Code lê ou edita arquivos daquela subpasta.

## Mapa dos níveis

| Nível | Escopo | Arquivo no projeto | Local de instalação real | Tipo de informação | Versionado? |
|---|---|---|---|---|---|
| 1 | **Política gerenciada** (organização) | [`hierarquia/nivel1-managed-policy/CLAUDE.md`](../hierarquia/nivel1-managed-policy/CLAUDE.md) | `/etc/claude-code/CLAUDE.md` (Linux/WSL) | Regras de compliance que ninguém sobrescreve: LGPD e dados de pacientes, proibição de acesso a produção, aprovação de dependências | Pela TI, fora do repo |
| 2 | **Usuário** (todos os projetos de uma pessoa) | [`hierarquia/nivel2-usuario/CLAUDE.md`](../hierarquia/nivel2-usuario/CLAUDE.md) | `~/.claude/CLAUDE.md` | Preferências pessoais: idioma das respostas, nível de detalhe, avisar antes de editar vários arquivos | Não |
| 3 | **Projeto** (compartilhado pela squad) | [`CLAUDE.md`](../CLAUDE.md) | raiz do repositório | Visão geral dos subprojetos, comando de testes global, fonte da verdade, fluxo spec-driven, ações proibidas | Sim |
| 4 | **Projeto local** (pessoal, neste projeto) | [`CLAUDE.local.md`](../CLAUDE.local.md) | raiz do repositório, no `.gitignore` | Ambiente da máquina (WSL, `python3`), em que funcionalidade a pessoa está trabalhando, preferência de saída | Não |
| 5 | **Subdiretório** (subprojeto) | [`backend/CLAUDE.md`](../backend/CLAUDE.md), [`scripts/migracao/CLAUDE.md`](../scripts/migracao/CLAUDE.md), [`relatorios/CLAUDE.md`](../relatorios/CLAUDE.md) | dentro de cada subpasta | Só as convenções daquele subprojeto: formatos de turno e testes (backend), CSV `latin-1` e dry-run (migração), somente leitura (relatórios) | Sim |

> Os níveis 1 e 2 ficam fora do repositório na instalação real. As cópias em `hierarquia/` servem para entrega e revisão. Para ativá-los: `sudo cp hierarquia/nivel1-managed-policy/CLAUDE.md /etc/claude-code/CLAUDE.md` e `cp hierarquia/nivel2-usuario/CLAUDE.md ~/.claude/CLAUDE.md`.

## Para onde foi cada parte do CLAUDE.md original

| Conteúdo do `/init` | Destino | Motivo |
|---|---|---|
| Visão geral e o fato de `scripts/` e `relatorios/` importarem `backend/` | Nível 3 | Afeta todos os subprojetos |
| Comando para rodar todos os testes | Nível 3 | Usado por todos antes de cada PR |
| Comando de um teste isolado | Nível 5, `backend/` | Só interessa a quem mexe no backend |
| Tabela de formatos de turno | Nível 5, `backend/` | Só quem toca `normalizar_turno` precisa dela. O nível 3 só avisa que os formatos são diferentes e diz onde está a tabela |
| Comando da migração e dry-run | Nível 5, `scripts/migracao/` | É uma convenção do subprojeto |
| Comando do relatório | Nível 5, `relatorios/` | É uma convenção do subprojeto |
| *(novo)* LGPD e proibição de produção | Nível 1 | Vale para todos os projetos da organização |
| *(novo)* Idioma e estilo de resposta | Nível 2 | É preferência pessoal |
| *(novo)* WSL e funcionalidade em andamento | Nível 4 | Pessoal e específico deste projeto |

## Como evitar duplicação

- **Nenhuma regra aparece em dois níveis.** Por exemplo, a regra "rodar a migração sem `--aplicar`" está só em `scripts/migracao/CLAUDE.md`. O nível 3 diz apenas que `--aplicar` é proibido sem um humano, que é a regra de segurança, e não repete como o script funciona.
- **Cada nível começa com uma linha indicando o próprio nível**, para que o time saiba onde colocar cada informação nova.
- **Quando algo do nível superior precisa ser lembrado, o nível de baixo faz referência** em vez de copiar. O nível 3, por exemplo, aponta para a tabela de formatos com "veja `backend/CLAUDE.md`".
