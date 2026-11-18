#!/usr/bin/env bash
# Conduz uma sessão real do Claude Code com várias rodadas (headless, -p + --resume)
# e grava cada rodada (prompt + resposta + session_id) num log Markdown.
#
# Uso: rodar_sessao.sh <diretorio-do-projeto> <arquivo-de-prompts> <log-de-saida>
#   O arquivo de prompts tem um prompt por bloco, separados por uma linha contendo só "---".
#   Um bloco que começa com "/clear" encerra a sessão atual e inicia uma nova (equivale ao /clear).
set -euo pipefail
CL="${CLAUDE_BIN:-$HOME/.vscode-server/extensions/anthropic.claude-code-2.1.281-linux-x64/resources/native-binary/claude}"
PROJ="$1"; PROMPTS="$2"; LOG="$3"
TOOLS="Read,Grep,Glob,Edit,Write,Bash(python3 -m unittest*),Bash(git diff*),Bash(git status*)"
SID=""
n=0
: > "$LOG"
echo "# Transcrição da sessão — $(date '+%Y-%m-%d %H:%M')" >> "$LOG"
echo "Projeto: \`$PROJ\` · Claude Code $("$CL" --version)" >> "$LOG"

python3 -I -c 'import sys,json;print(json.dumps(open(sys.argv[1],encoding="utf-8").read().split("\n---\n")))' "$PROMPTS" > /tmp/prompts.json
total=$(python3 -I -c 'import json;print(len(json.load(open("/tmp/prompts.json"))))')

for ((i=0; i<total; i++)); do
  P=$(python3 -I -c 'import json,sys;print(json.load(open("/tmp/prompts.json"))[int(sys.argv[1])].strip())' "$i")
  if [[ "$P" == /clear* ]]; then
    SID=""
    echo -e "\n---\n\n### >>> /clear — contexto descartado, nova sessão\n" >> "$LOG"
    P="${P#/clear}"; P="$(echo "$P" | sed '/./,$!d')"
    [[ -z "$P" ]] && continue
  fi
  n=$((n+1))
  ARGS=(-p "$P" --model sonnet --output-format json --allowedTools "$TOOLS")
  [[ -n "$SID" ]] && ARGS+=(--resume "$SID")
  [[ -z "$SID" && -n "${NOME_SESSAO:-}" ]] && ARGS+=(-n "$NOME_SESSAO")
  [[ -z "$SID" && -n "${RETOMAR:-}" ]] && ARGS+=(--resume "$RETOMAR")
  OUT=$(cd "$PROJ" && "$CL" "${ARGS[@]}" 2>/dev/null)
  SID=$(echo "$OUT" | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')
  RES=$(echo "$OUT" | python3 -I -c 'import sys,json;d=json.load(sys.stdin);print(d.get("result",""))')
  TURNS=$(echo "$OUT" | python3 -I -c 'import sys,json;print(json.load(sys.stdin).get("num_turns"))')
  {
    echo -e "\n---\n\n## Rodada $n  ·  session_id \`$SID\`  ·  $TURNS turnos internos\n"
    echo "**Usuário:**"; echo; echo "$P" | sed 's/^/> /'; echo
    echo "**Claude Code:**"; echo; echo "$RES"
  } >> "$LOG"
  echo "rodada $n ok ($SID)"
done
