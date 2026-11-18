"""Validação dos arquivos de turno de ``config/``.

Detecta o formato como ``normalizar_turno``: a presença de ``janela`` indica o
formato da tarde; caso contrário vale o formato da manhã.
"""

from __future__ import annotations

from datetime import datetime, time

CHAVES_MANHA = ("turno", "inicio", "fim", "duracao_consulta_min", "dias")
CHAVES_TARDE = ("turno", "janela", "duracao_minutos", "dias_semana")


def _hora(valor) -> time | None:
    if not isinstance(valor, str):
        return None
    try:
        return datetime.strptime(valor, "%H:%M").time()
    except ValueError:
        return None


def _checar_horario(rotulo: str, valor, erros: list[str]) -> time | None:
    hora = _hora(valor)
    if hora is None:
        erros.append(f"{rotulo}: horário inválido {valor!r} (esperado HH:MM)")
    return hora


def _checar_duracao(rotulo: str, valor, erros: list[str]) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        erros.append(f"{rotulo}: duração deve ser um inteiro positivo, recebido {valor!r}")


def validar_turno(dados: dict) -> list[str]:
    """Retorna a lista de erros de um dicionário de turno (vazia se válido)."""
    if not isinstance(dados, dict):
        return ["turno deve ser um objeto"]

    erros: list[str] = []
    tarde = "janela" in dados
    obrigatorias = CHAVES_TARDE if tarde else CHAVES_MANHA
    for chave in obrigatorias:
        if chave not in dados:
            erros.append(f"chave obrigatória ausente: {chave}")

    if tarde:
        janela = dados.get("janela")
        inicio = fim = None
        if "janela" in dados:
            if not isinstance(janela, dict):
                erros.append("janela deve ser um objeto com abre/fecha")
            else:
                for chave in ("abre", "fecha"):
                    if chave not in janela:
                        erros.append(f"chave obrigatória ausente: janela.{chave}")
                if "abre" in janela:
                    inicio = _checar_horario("janela.abre", janela["abre"], erros)
                if "fecha" in janela:
                    fim = _checar_horario("janela.fecha", janela["fecha"], erros)
        if "duracao_minutos" in dados:
            _checar_duracao("duracao_minutos", dados["duracao_minutos"], erros)
        for i, pausa in enumerate(dados.get("pausas", [])):
            if not isinstance(pausa, dict) or "de" not in pausa or "ate" not in pausa:
                erros.append(f"pausas[{i}]: esperado objeto com de/ate")
                continue
            de = _checar_horario(f"pausas[{i}].de", pausa["de"], erros)
            ate = _checar_horario(f"pausas[{i}].ate", pausa["ate"], erros)
            if de and ate and ate <= de:
                erros.append(f"pausas[{i}]: ate deve ser depois de de")
    else:
        inicio = fim = None
        if "inicio" in dados:
            inicio = _checar_horario("inicio", dados["inicio"], erros)
        if "fim" in dados:
            fim = _checar_horario("fim", dados["fim"], erros)
        if "duracao_consulta_min" in dados:
            _checar_duracao("duracao_consulta_min", dados["duracao_consulta_min"], erros)

    if inicio and fim and fim <= inicio:
        erros.append("fim deve ser depois do início")

    return erros
