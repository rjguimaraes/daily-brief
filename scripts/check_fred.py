"""Confere se a chave FRED (secret FRED_API_KEY) funciona, sem expor a chave."""
import json
import os
from pathlib import Path

import requests

key = os.environ.get("FRED_API_KEY", "")
out = Path("reports/probe/fred_check.json")
result = {"chave_presente": bool(key), "chave_tamanho": len(key)}
if key:
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": "SP500", "api_key": key, "file_type": "json",
                "observation_start": "2026-09-25", "sort_order": "desc", "limit": 5},
        timeout=60,
    )
    result["status"] = r.status_code
    try:
        body = r.json()
        result["ultimas_observacoes"] = [
            {"data": o["date"], "valor": o["value"]} for o in body.get("observations", [])
        ]
        if "error_message" in body:
            result["erro"] = body["error_message"].replace(key, "***")
    except ValueError:
        result["erro"] = "resposta não JSON"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
