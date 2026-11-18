"""Módulo de notificação de pacientes.

Monta mensagens a partir de templates e as entrega por um canal
(e-mail ou SMS). Os canais reais ainda não foram integrados: ``CanalConsole``
apenas registra as mensagens enviadas, o que também é usado nos testes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

TEMPLATES = {
    "confirmacao": "Olá, {nome}! Sua consulta está confirmada para {quando}.",
    "lembrete": "Olá, {nome}! Lembrete: você tem consulta em {quando}.",
}


class Canal(Protocol):
    def enviar(self, destino: str, mensagem: str) -> None: ...


@dataclass
class CanalConsole:
    enviadas: list[tuple[str, str]] = field(default_factory=list)

    def enviar(self, destino: str, mensagem: str) -> None:
        self.enviadas.append((destino, mensagem))
        print(f"[notificacao] -> {destino}: {mensagem}")


class Notificador:
    def __init__(self, canal: Canal) -> None:
        self.canal = canal

    def notificar(self, tipo: str, destino: str, nome: str, quando: datetime) -> str:
        if tipo not in TEMPLATES:
            raise ValueError(f"Tipo de notificação desconhecido: {tipo}")
        mensagem = TEMPLATES[tipo].format(nome=nome, quando=quando.strftime("%d/%m/%Y %H:%M"))
        self.canal.enviar(destino, mensagem)
        return mensagem
