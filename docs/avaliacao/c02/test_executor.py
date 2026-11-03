"""Confere a classificação do instrumento; estes tempos NÃO integram o C02."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("executor_c02", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


@pytest.mark.parametrize("resultado", ["resposta", "ausencia", "excecao"])
def test_classifica_falha_mesmo_quando_chat_service_captura(monkeypatch, tmp_path, resultado):
    """ChatService, estado, banco e auditoria reais; fronteira NLP controlada."""
    class NLP:
        def __init__(self, retriever):
            pass

        def process(self, text, user_name=None):
            if resultado == "excecao":
                raise RuntimeError("Falha sintetica")
            return "Resposta sintetica" if resultado == "resposta" else None

    fake_setup = ModuleType("app.main")
    fake_setup.setup_system = lambda: {"servicos": object()}
    fake_setup.METRICAS_INDEXACAO = {}
    fake_nlp = ModuleType("api.services.nlp_service")
    fake_nlp.NLPService = NLP
    fake_rag = ModuleType("app.core.rag_pipeline")
    fake_rag.MODEL_NAME = "sintetico"
    fake_rag.get_llm = lambda: SimpleNamespace(temperature=0.1, max_tokens=500, max_retries=2, request_timeout=None)
    for name, module in [("app.main", fake_setup), ("api.services.nlp_service", fake_nlp), ("app.core.rag_pipeline", fake_rag)]:
        monkeypatch.setitem(sys.modules, name, module)
    import app.core
    monkeypatch.setattr(app.core, "rag_pipeline", fake_rag, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "somente-teste-sem-rede")
    success = executor.messages(SimpleNamespace(escopo="rag", modelo=None), tmp_path)
    assert success is (resultado == "resposta")
    rows = json.loads((tmp_path / "mensagens.json").read_text(encoding="utf-8"))
    measured = [r for r in rows if r["fase"] == "medicao"]
    assert len(measured) == 30
    assert all(r["sucesso"] is (resultado == "resposta") for r in measured)
    if resultado == "excecao":
        # Texto livre registra MESSAGE_SENT apesar da exceção; instrumento deve reprovar.
        free = [r for r in measured if r["percurso"] == "texto_livre"]
        assert all(any(e["tipo"] == "MESSAGE_SENT" for e in r["eventos"]) for r in free)
        assert all(r["nlp"][0]["erro_tipo"] == "RuntimeError" for r in free)
        menu = [r for r in measured if r["percurso"] == "menu_rag"]
        assert all(any(e["tipo"] == "MESSAGE_FAILED" for e in r["eventos"]) for r in menu)
    summary = json.loads((tmp_path / "resumo.json").read_text(encoding="utf-8"))
    assert summary["texto_livre"]["total_ms_sucessos"]["n"] == (15 if resultado == "resposta" else 0)


def test_credencial_ausente_nao_vira_trinta_falhas_medidas(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert not executor.messages(SimpleNamespace(escopo="rag", modelo=None), tmp_path)
    assert not (tmp_path / "mensagens.json").exists()
    assert json.loads((tmp_path / "impedimento.json").read_text(encoding="utf-8"))["mensagens_medidas"] == 0
