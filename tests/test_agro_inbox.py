"""Pacote do agro enviado pelo notebook: mesmos parsers da coleta direta."""
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dbrief import collectors as col  # noqa: E402

RAW = Path(__file__).resolve().parents[1] / "reports" / "probe" / "raw"


class AgroInbox(unittest.TestCase):
    def test_pacote(self):
        files = {
            "boi_gordo_sp__recente.html": "na_boi.html",
            "boi_gordo_sp__2025-12-30.html": "na_boi_data_2025-12-30.html",
            "scot__recente.html": "na_scot.html",
            "datagro__2025-12-30.html": "na_reposicao_nelore_macho_2025-12-30.html",
        }
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "t.zip"
            with zipfile.ZipFile(z, "w") as zf:
                for name, src in files.items():
                    zf.write(RAW / src, name)
                zf.writestr("milho_cepea__2026-11-18.html", "<html>vazio</html>")
                zf.writestr("leia-me.txt", "ignorar")
            out = col.agro_from_inbox(str(z), log=lambda m: None)
        self.assertIn((date(2025, 12, 30), 319.2), out["boi_gordo_sp"])
        self.assertEqual(out["boi_comum_go_sul"], [(date(2026, 10, 8), 349.0)])
        self.assertEqual([p[0] for p in out["bezerro_to"]], [date(2025, 12, 30)])
        self.assertNotIn("milho_cepea", out)


if __name__ == "__main__":
    unittest.main()
