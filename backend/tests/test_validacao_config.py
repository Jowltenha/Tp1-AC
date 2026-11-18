"""Testes do validador de arquivos de turno."""

import json
import unittest

from agendamento.disponibilidade import CONFIG_DIR
from agendamento.validacao_config import validar_turno


class TestValidarTurno(unittest.TestCase):
    def test_arquivos_reais_de_config_sao_validos(self):
        arquivos = sorted(CONFIG_DIR.glob("horarios-*.json"))
        self.assertEqual(len(arquivos), 2)
        for arq in arquivos:
            with self.subTest(arquivo=arq.name):
                dados = json.loads(arq.read_text(encoding="utf-8"))
                self.assertEqual(validar_turno(dados), [])

    def test_turno_invalido_acumula_erros(self):
        erros = validar_turno({"turno": "manha", "inicio": "12:00", "fim": "08:00",
                               "duracao_consulta_min": 0})
        self.assertIn("fim deve ser depois do início", erros)
        self.assertIn("chave obrigatória ausente: dias", erros)
        self.assertTrue(any("duracao_consulta_min" in e for e in erros))

    def test_horario_malformado_na_tarde(self):
        erros = validar_turno({"turno": "tarde", "janela": {"abre": "25:99", "fecha": "18:00"},
                               "duracao_minutos": 45, "dias_semana": [1]})
        self.assertTrue(any("janela.abre" in e for e in erros))


if __name__ == "__main__":
    unittest.main()
