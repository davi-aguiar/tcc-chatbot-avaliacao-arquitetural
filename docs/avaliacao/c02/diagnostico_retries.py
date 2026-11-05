"""Diagnóstico C02, fora das séries: tentativas HTTP por geração. Não grava corpo, chave nem autorização."""
import json
import os
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"

MODELO, SAIDA = sys.argv[1], Path(sys.argv[2])
CABECALHOS = ("retry-after", "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens",
              "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests")
tentativas = []
envio_real = httpx.Client.send


def envio_observado(self, request, **kwargs):
    inicio = time.perf_counter()
    resposta = envio_real(self, request, **kwargs)
    tentativas.append({
        "status": resposta.status_code, "duracao_ms": round((time.perf_counter() - inicio) * 1000, 1),
        "retry_count": request.headers.get("x-stainless-retry-count"),
        "cabecalhos": {k: resposta.headers[k] for k in CABECALHOS if k in resposta.headers},
    })
    return resposta


httpx.Client.send = envio_observado

from app.main import setup_system
from api.services.nlp_service import NLPService
from app.core import rag_pipeline

rag_pipeline.MODEL_NAME = MODELO
rag_pipeline.CACHED_LLM = None
nlp = NLPService(setup_system()["servicos"])
casos = [c for c in json.loads((ROOT / "docs/avaliacao/c02/casos.json").read_text(encoding="utf-8")) if c["percurso"] != "estatico"]
geracoes = []
for rodada in (1, 2):
    for caso in casos:
        tentativas.clear()
        inicio = time.perf_counter()
        try:
            resposta = nlp.process(caso["consulta"])
            erro = None
        except Exception as exc:
            resposta, erro = None, type(exc).__name__
        geracoes.append({"rodada": rodada, "caso": caso["id"], "total_ms": round((time.perf_counter() - inicio) * 1000, 1),
                         "tem_resposta": bool(resposta), "erro_tipo": erro, "tentativas_http": list(tentativas)})
        print(rodada, caso["id"], geracoes[-1]["total_ms"], [t["status"] for t in tentativas], flush=True)
        SAIDA.write_text(json.dumps({"modelo": MODELO, "geracoes": geracoes}, ensure_ascii=False, indent=2), encoding="utf-8")
