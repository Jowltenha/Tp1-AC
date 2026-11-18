"""Testes dos módulos do backend (unittest, sem dependências externas).

Executar a partir da raiz do repositório:
    python3 -m unittest discover -s backend/tests -t backend
"""

import unittest
from datetime import date, datetime

from agendamento.disponibilidade import carregar_agenda, normalizar_turno
from agendamento.notificacao import CanalConsole, Notificador
from agendamento.pacientes import RepositorioPacientes, cpf_valido


class TestDisponibilidade(unittest.TestCase):
    def setUp(self):
        self.agenda = carregar_agenda()

    def test_normaliza_os_dois_formatos(self):
        manha = normalizar_turno({"turno": "manha", "inicio": "08:00", "fim": "12:00",
                                  "duracao_consulta_min": 30, "dias": ["seg"]})
        tarde = normalizar_turno({"turno": "tarde", "janela": {"abre": "13:30", "fecha": "18:00"},
                                  "duracao_minutos": 45, "dias_semana": [1]})
        self.assertEqual(manha.duracao_min, 30)
        self.assertEqual(tarde.duracao_min, 45)
        self.assertEqual(tarde.dias, ("seg",))

    def test_sexta_so_tem_manha(self):
        slots = self.agenda.slots_do_dia("med-1", date(2026, 11, 20))  # sexta
        self.assertTrue(all(s.hour < 12 for s in slots))
        self.assertEqual(len(slots), 8)

    def test_pausa_da_tarde_e_respeitada(self):
        slots = self.agenda.slots_do_dia("med-1", date(2026, 11, 16))  # segunda
        self.assertNotIn(datetime(2026, 11, 16, 15, 45), slots)

    def test_reservar_e_liberar(self):
        inicio = datetime(2026, 11, 16, 8, 0)
        self.agenda.reservar("med-1", inicio)
        with self.assertRaises(ValueError):
            self.agenda.reservar("med-1", inicio)
        self.agenda.liberar("med-1", inicio)
        self.agenda.reservar("med-1", inicio)


class TestPacientes(unittest.TestCase):
    def test_cpf(self):
        self.assertTrue(cpf_valido("529.982.247-25"))
        self.assertFalse(cpf_valido("111.111.111-11"))

    def test_cadastro_duplicado(self):
        repo = RepositorioPacientes()
        repo.cadastrar("Ana", "529.982.247-25", "ana@exemplo.com")
        with self.assertRaises(ValueError):
            repo.cadastrar("Ana", "52998224725", "ana@exemplo.com")


class TestNotificacao(unittest.TestCase):
    def test_confirmacao(self):
        canal = CanalConsole()
        msg = Notificador(canal).notificar("confirmacao", "ana@exemplo.com", "Ana",
                                           datetime(2026, 11, 16, 8, 0))
        self.assertIn("16/11/2026 08:00", msg)
        self.assertEqual(len(canal.enviadas), 1)


if __name__ == "__main__":
    unittest.main()
