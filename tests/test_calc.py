"""Testes das fórmulas e regras do Painel. Rodar: python -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dbrief import calc, store  # noqa: E402
from dbrief.collectors import br_number  # noqa: E402


class TestFormulas(unittest.TestCase):
    def test_pct(self):
        self.assertAlmostEqual(calc.pct_change(110, 100), 10.0)
        self.assertAlmostEqual(calc.pct_change(90, 100), -10.0)

    def test_bp_exemplo_da_especificacao(self):
        # de 4,20% para 4,70% = +50 pontos-base
        self.assertAlmostEqual(calc.bp_change(4.70, 4.20), 50.0)

    def test_change_por_tipo(self):
        self.assertAlmostEqual(calc.change("taxa", 13.75, 14.25), -50.0)
        self.assertAlmostEqual(calc.change("preco", 5.5, 5.0), 10.0)
        with self.assertRaises(ValueError):
            calc.change("outro", 1, 1)

    def test_br_number(self):
        self.assertEqual(br_number("3.066,58"), 3066.58)
        self.assertEqual(br_number("209.066,90"), 209066.90)
        self.assertEqual(br_number("67,18"), 67.18)


class TestDatas(unittest.TestCase):
    def test_minus_months_fim_de_mes(self):
        self.assertEqual(calc.minus_months(date(2026, 3, 31), 1), date(2026, 2, 28))
        self.assertEqual(calc.minus_months(date(2024, 3, 31), 1), date(2024, 2, 29))
        self.assertEqual(calc.minus_months(date(2026, 1, 15), 1), date(2025, 12, 15))
        self.assertEqual(calc.minus_months(date(2026, 10, 9), 12), date(2025, 10, 9))

    def test_as_of_nunca_olha_para_frente(self):
        ds = [date(2026, 10, 2), date(2026, 10, 5)]
        self.assertEqual(calc.as_of(ds, date(2026, 10, 4)), date(2026, 10, 2))  # fim de semana
        self.assertEqual(calc.as_of(ds, date(2026, 10, 5)), date(2026, 10, 5))
        self.assertIsNone(calc.as_of(ds, date(2026, 10, 1)))


class TestComputeRow(unittest.TestCase):
    def setUp(self):
        self.s = {
            date(2025, 10, 8): 100.0,   # ~1 ano antes (09/10/25 não existe → usa 08/10)
            date(2025, 12, 30): 120.0,  # último fechamento de 2025
            date(2026, 9, 9): 150.0,    # ~1 mês antes
            date(2026, 10, 9): 165.0,   # atual
        }

    def test_comparativos(self):
        r = calc.compute_row(self.s, "preco", date(2026, 10, 10), 4)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["atual"]["data"], "2026-10-09")
        self.assertAlmostEqual(r["m1"]["variacao"], 10.0)
        self.assertEqual(r["ytd"]["data_ref"], "2025-12-30")
        self.assertAlmostEqual(r["ytd"]["variacao"], 37.5)
        self.assertEqual(r["y1"]["data_ref"], "2025-10-08")
        self.assertAlmostEqual(r["y1"]["variacao"], 65.0)

    def test_defasado(self):
        r = calc.compute_row(self.s, "preco", date(2026, 10, 20), 4)
        self.assertEqual(r["status"], "defasado")

    def test_referencia_distante_vira_ausente_com_motivo(self):
        s = {date(2026, 8, 1): 1.0, date(2026, 10, 9): 2.0}
        r = calc.compute_row(s, "preco", date(2026, 10, 9), 4)
        self.assertNotIn("variacao", r["m1"])
        self.assertIn("motivo", r["m1"])
        self.assertIn("histórico começa", r["y1"]["motivo"])

    def test_taxa_em_pontos_base(self):
        s = {date(2025, 12, 31): 15.0, date(2026, 9, 9): 14.25, date(2026, 10, 9): 13.75}
        r = calc.compute_row(s, "taxa", date(2026, 10, 9), 4)
        self.assertAlmostEqual(r["m1"]["variacao"], -50.0)
        self.assertAlmostEqual(r["ytd"]["variacao"], -125.0)
        self.assertEqual(r["m1"]["unidade_variacao"], "pb")

    def test_serie_vazia(self):
        self.assertEqual(calc.compute_row({}, "preco", date(2026, 10, 9), 4)["status"], "ausente")


class TestRelacaoESaltos(unittest.TestCase):
    def test_relacao_mesma_data(self):
        bez = {date(2026, 10, 8): 3478.44, date(2026, 10, 9): 3481.33}
        boi = {date(2026, 10, 8): 376.30}
        r = calc.ratio_series(bez, boi)
        self.assertEqual(list(r), [date(2026, 10, 8)])
        self.assertAlmostEqual(r[date(2026, 10, 8)], 3478.44 / 376.30)

    def test_saltos(self):
        s = {date(2026, 10, 1): 100.0, date(2026, 10, 2): 130.0}
        self.assertEqual(len(calc.daily_jumps(s, 10, date(2026, 9, 1))), 1)
        self.assertEqual(len(calc.daily_jumps(s, 50, date(2026, 9, 1))), 0)


class TestStore(unittest.TestCase):
    def test_upsert_revisao_e_futuro(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            today = date(2026, 10, 9)
            r1 = store.upsert("x", [(date(2026, 10, 8), 1.0), (date(2026, 11, 4), 9.0)], "f", "m", today, base)
            self.assertEqual((r1["novos"], r1["futuros_descartados"]), (1, 1))
            r2 = store.upsert("x", [(date(2026, 10, 8), 1.5)], "f", "m", today, base)
            self.assertEqual(r2["revisados"][0]["depois"], 1.5)
            self.assertEqual(store.load("x", base)[date(2026, 10, 8)].valor, 1.5)


if __name__ == "__main__":
    unittest.main()
