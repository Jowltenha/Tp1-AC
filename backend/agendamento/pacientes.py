"""Módulo de cadastro de pacientes.

Mantém um repositório em memória de pacientes, com validação de CPF e
e-mail. Em produção o repositório será substituído por persistência real;
a interface pública (``cadastrar``, ``buscar_por_cpf``, ``atualizar_contato``)
deve ser preservada.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass


@dataclass
class Paciente:
    id: str
    nome: str
    cpf: str
    email: str
    telefone: str | None = None


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def cpf_valido(cpf: str) -> bool:
    numeros = _so_digitos(cpf)
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * (tamanho + 1 - i) for i, d in enumerate(numeros[:tamanho]))
        digito = (soma * 10) % 11 % 10
        if digito != int(numeros[tamanho]):
            return False
    return True


def email_valido(email: str) -> bool:
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


class RepositorioPacientes:
    def __init__(self) -> None:
        self._por_cpf: dict[str, Paciente] = {}

    def cadastrar(self, nome: str, cpf: str, email: str, telefone: str | None = None) -> Paciente:
        cpf_limpo = _so_digitos(cpf)
        if not cpf_valido(cpf_limpo):
            raise ValueError("CPF inválido")
        if not email_valido(email):
            raise ValueError("E-mail inválido")
        if cpf_limpo in self._por_cpf:
            raise ValueError("Paciente já cadastrado")
        paciente = Paciente(str(uuid.uuid4()), nome.strip(), cpf_limpo, email, telefone)
        self._por_cpf[cpf_limpo] = paciente
        return paciente

    def buscar_por_cpf(self, cpf: str) -> Paciente | None:
        return self._por_cpf.get(_so_digitos(cpf))

    def atualizar_contato(self, cpf: str, email: str | None = None, telefone: str | None = None) -> Paciente:
        paciente = self.buscar_por_cpf(cpf)
        if paciente is None:
            raise KeyError("Paciente não encontrado")
        if email is not None:
            if not email_valido(email):
                raise ValueError("E-mail inválido")
            paciente.email = email
        if telefone is not None:
            paciente.telefone = telefone
        return paciente
