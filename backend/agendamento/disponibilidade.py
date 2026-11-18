"""Módulo de disponibilidade de horários.

Lê os arquivos de configuração de turnos em ``config/`` e gera os slots de
consulta disponíveis por médico e data. Também mantém o registro em memória
dos slots já reservados.

Atenção: os arquivos de turno têm formatos diferentes
(``horarios-manha.json`` usa ``inicio``/``fim``; ``horarios-tarde.json`` usa
``janela.abre``/``janela.fecha`` e uma lista de ``pausas``). A função
``normalizar_turno`` converte ambos para o mesmo formato interno.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


@dataclass(frozen=True)
class Turno:
    nome: str
    inicio: time
    fim: time
    duracao_min: int
    dias: tuple[str, ...]
    pausas: tuple[tuple[time, time], ...] = ()


@dataclass
class AgendaDisponibilidade:
    turnos: list[Turno]
    reservados: set[tuple[str, datetime]] = field(default_factory=set)

    def slots_do_dia(self, medico_id: str, dia: date) -> list[datetime]:
        """Retorna os horários livres de um médico em uma data."""
        sigla = DIAS_SEMANA[dia.weekday()]
        livres: list[datetime] = []
        for turno in self.turnos:
            if sigla not in turno.dias:
                continue
            atual = datetime.combine(dia, turno.inicio)
            limite = datetime.combine(dia, turno.fim)
            passo = timedelta(minutes=turno.duracao_min)
            while atual + passo <= limite:
                if not _em_pausa(atual.time(), turno.pausas) and (
                    medico_id,
                    atual,
                ) not in self.reservados:
                    livres.append(atual)
                atual += passo
        return livres

    def reservar(self, medico_id: str, inicio: datetime) -> None:
        if inicio not in self.slots_do_dia(medico_id, inicio.date()):
            raise ValueError(f"Horário indisponível: {inicio:%Y-%m-%d %H:%M}")
        self.reservados.add((medico_id, inicio))

    def liberar(self, medico_id: str, inicio: datetime) -> None:
        """Devolve um slot reservado à agenda (usado em cancelamentos)."""
        self.reservados.discard((medico_id, inicio))


def _em_pausa(h: time, pausas: tuple[tuple[time, time], ...]) -> bool:
    return any(ini <= h < fim for ini, fim in pausas)


def _hora(texto: str) -> time:
    return datetime.strptime(texto, "%H:%M").time()


def normalizar_turno(dados: dict) -> Turno:
    """Converte qualquer um dos dois formatos de arquivo de turno em ``Turno``."""
    if "janela" in dados:  # formato da tarde
        inicio, fim = dados["janela"]["abre"], dados["janela"]["fecha"]
        duracao = dados["duracao_minutos"]
        dias = tuple(DIAS_SEMANA[n - 1] for n in dados["dias_semana"])
        pausas = tuple((_hora(p["de"]), _hora(p["ate"])) for p in dados.get("pausas", []))
    else:  # formato da manhã
        inicio, fim = dados["inicio"], dados["fim"]
        duracao = dados["duracao_consulta_min"]
        dias = tuple(dados["dias"])
        pausas = ()
    return Turno(dados["turno"], _hora(inicio), _hora(fim), duracao, dias, pausas)


def carregar_agenda(config_dir: Path = CONFIG_DIR) -> AgendaDisponibilidade:
    turnos = [
        normalizar_turno(json.loads(arq.read_text(encoding="utf-8")))
        for arq in sorted(config_dir.glob("horarios-*.json"))
    ]
    return AgendaDisponibilidade(turnos)
