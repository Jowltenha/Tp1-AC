"""Migração de pacientes do sistema legado (CSV) para o novo serviço.

Uso:
    python3 scripts/migracao/migrar_pacientes_legado.py <arquivo.csv>            # dry-run (padrão)
    python3 scripts/migracao/migrar_pacientes_legado.py <arquivo.csv> --aplicar  # grava de fato

Formato do CSV legado (separador ';', encoding latin-1):
    NOME;CPF;EMAIL;FONE
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from agendamento.pacientes import RepositorioPacientes  # noqa: E402


def migrar(caminho: Path, aplicar: bool) -> dict[str, int]:
    repo = RepositorioPacientes()
    resumo = {"lidos": 0, "migrados": 0, "rejeitados": 0}
    with caminho.open(encoding="latin-1", newline="") as arq:
        for linha in csv.DictReader(arq, delimiter=";"):
            resumo["lidos"] += 1
            try:
                repo.cadastrar(linha["NOME"], linha["CPF"], linha["EMAIL"].strip().lower(),
                               linha.get("FONE") or None)
                resumo["migrados"] += 1
            except ValueError as erro:
                resumo["rejeitados"] += 1
                print(f"[rejeitado] linha {resumo['lidos']}: {erro}", file=sys.stderr)
    modo = "APLICADO" if aplicar else "DRY-RUN"
    print(f"[{modo}] {resumo}")
    return resumo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", type=Path)
    parser.add_argument("--aplicar", action="store_true", help="grava de fato (padrão: dry-run)")
    args = parser.parse_args()
    migrar(args.csv, args.aplicar)
