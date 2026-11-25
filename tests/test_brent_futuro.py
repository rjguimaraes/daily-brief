"""Brent futuro (Yahoo, BZ=F) no pacote do notebook."""
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dbrief import collectors as col  # noqa: E402

NY = ZoneInfo("America/New_York")


def ts(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=NY).timestamp())


def chart(stamps, closes, rmt, end):
    return json.dumps({"chart": {"error": None, "result": [{
        "meta": {"symbol": "BZ=F", "exchangeTimezoneName": "America/New_York",
                 "regularMarketTime": rmt, "currentTradingPeriod": {"regular": {"end": end}}},
        "timestamp": stamps, "indicators": {"quote": [{"close": closes}]}}]}})


class BrentFuturo(unittest.TestCase):
    def test_fechamentos_e_barra_aberta(self):
        stamps = [ts(2026, 11, 20), ts(2026, 11, 23), ts(2026, 11, 24), ts(2026, 11, 25)]
        closes = [93.1, None, 91.004, 92.5]
        # pregão de 25/11 ainda aberto: a barra de 25/11 sai
        txt = chart(stamps, closes, ts(2026, 11, 25, 10), ts(2026, 11, 25, 17))
        self.assertEqual(col.parse_yahoo_chart(txt),
                         [(date(2026, 11, 20), 93.1), (date(2026, 11, 24), 91.0)])
        # depois do fim do pregão: entra
        txt = chart(stamps, closes, ts(2026, 11, 25, 17, ), ts(2026, 11, 25, 17))
        self.assertEqual(col.parse_yahoo_chart(txt)[-1], (date(2026, 11, 25), 92.5))

    def test_barra_marcada_na_noite_anterior(self):
        txt = chart([ts(2026, 11, 23, 18)], [90.0], ts(2026, 11, 25, 18), ts(2026, 11, 25, 17))
        self.assertEqual(col.parse_yahoo_chart(txt), [(date(2026, 11, 24), 90.0)])

    def test_erro(self):
        with self.assertRaises(RuntimeError):
            col.parse_yahoo_chart(json.dumps({"chart": {"result": None, "error": {"code": "Not Found"}}}))

    def test_pacote(self):
        txt = chart([ts(2026, 11, 24)], [91.0], ts(2026, 11, 24, 17), ts(2026, 11, 24, 17))
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "t.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("brent_futuro__recente.json", txt)
            out = col.agro_from_inbox(str(z), log=lambda m: None)
        self.assertEqual(out["brent_futuro"], [(date(2026, 11, 24), 91.0)])


if __name__ == "__main__":
    unittest.main()
