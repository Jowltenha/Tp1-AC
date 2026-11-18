"""Automação interna: relatório semanal de ocupação da agenda.

Gera um CSV com o número de slots disponíveis por dia da semana, a partir
das configurações de turno. Só lê dados — nunca altera a agenda.

Uso:
    python3 relatorios/relatorio_ocupacao.py [--saida relatorios/saida/ocupacao.csv]
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from agendamento.disponibilidade import carregar_agenda  # noqa: E402


def gerar(inicio: date, saida: Path) -> None:
    agenda = carregar_agenda()
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as arq:
        escritor = csv.writer(arq)
        escritor.writerow(["data", "slots_disponiveis"])
        for i in range(7):
            dia = inicio + timedelta(days=i)
            escritor.writerow([dia.isoformat(), len(agenda.slots_do_dia("todos", dia))])
    print(f"Relatório gravado em {saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", type=Path, default=Path("relatorios/saida/ocupacao.csv"))
    args = parser.parse_args()
    hoje = date.today()
    gerar(hoje - timedelta(days=hoje.weekday()), args.saida)
