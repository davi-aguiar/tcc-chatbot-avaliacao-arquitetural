"""Verifica isolamento HTTP e classificação do instrumento; fora da coleta C03-B."""
import asyncio
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

SPEC = importlib.util.spec_from_file_location("executor_c03b", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


def test_matriz_fixada_e_payloads():
    assert len(executor.cases("controlado")) == 21
    assert sum(size for _, _, size in executor.cases("controlado")) == 104
    assert executor.cases("real") == [("evolution", "rag_real", 1), ("evolution", "rag_real", 10)]
    path, payload = executor.body("evolution", "550000", "4")
    assert path == "/evolution_webhook"
    assert payload["data"]["key"]["remoteJid"] == "550000@s.whatsapp.net"


def test_http_em_outro_processo_distingue_bloqueio_timeout_e_queda(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, "cases", lambda mode: [
        ("rest", "estatico", 2), ("evolution", "rag_lento", 2),
        ("evolution", "limite_429", 1), ("evolution", "timeout_cliente", 5)])
    executor.save(tmp_path / "config.json", {"modo": "controlado", "modelo": "llama-3.3-70b-versatile", "atraso_s": 0.5})
    with (tmp_path / "servidor.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(executor.HERE / "servidor.py"), str(tmp_path)],
                                   cwd=executor.ROOT, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            rows = asyncio.run(executor.collect(tmp_path, process, "controlado"))
            process.wait(timeout=10)
            assert process.returncode == 0
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    assert len(rows) == 4
    assert rows[0]["resumo"]["inferencias_observadas"] == 0
    slow = rows[1]["resumo"]
    assert slow["inferencias_observadas"] == 2
    assert slow["inferencias_max_simultaneas"] == 1
    assert slow["saude_enviada_durante_espera"]
    assert slow["saude_executada_apos_espera"]
    assert rows[2]["resumo"]["status_provedor"] == {200: 1, 429: 1}
    assert rows[3]["resumo"]["erros_cliente"].get("ReadTimeout", 0) > 0
    assert all(r["resumo"]["processo_vivo_apos"] and r["resumo"]["drenagem_completa"]
               and r["resumo"]["saude_apos_ok"] and r["resumo"]["menu_apos_ok"] for r in rows)
    assert not any(e["evento"] == "rede_externa_bloqueada" for e in executor.read_events(tmp_path))
