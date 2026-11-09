"""Verificação do instrumento C03; não compõe a coleta arquitetural."""
import importlib.util
import json
from pathlib import Path
import socket

import pytest

SPEC = importlib.util.spec_from_file_location("executor_c03", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


def test_coleta_preserva_falhas_reais_e_distingue_auditoria(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = executor.collect(tmp_path)
    assert result["coleta_valida"]
    assert result["casos_executados"] == result["casos_atendidos"] == 12
    assert result["tentativas_rede"] == []
    rows = json.loads((tmp_path / "casos-executados.json").read_text(encoding="utf-8"))
    assert {r["erro_esperado"] for r in rows} == {"APITimeoutError", "APIConnectionError", "NotFoundError"}
    assert {r["repeticao"] for r in rows} == {1, 2}
    assert sum(len(r["retomada"]) for r in rows) == 48
    for row in rows:
        assert row["falha"]["nlp"][0]["mesma_excecao_injetada"]
        assert all(s["atendida"] for s in row["retomada"])
        assert len(row["sdk"]) == 1  # Injeção fica ativa na retomada.
        events = [e["tipo"] for e in row["falha"]["eventos"]]
        if row["percurso"] == "menu_rag":
            assert "MESSAGE_FAILED" in events and "MESSAGE_SENT" not in events
            assert row["falha"]["resposta"] == "Desculpe, ocorreu um erro interno."
            assert row["falha"]["mensagens_persistidas"] == []
        else:
            assert "MESSAGE_SENT" in events and "MESSAGE_FAILED" not in events
            assert row["falha"]["resposta"].startswith("Opção inválida.")
            assert len(row["falha"]["mensagens_persistidas"]) == 2


@pytest.mark.parametrize("missing", ["prompt", "sdk", "excecao"])
def test_injecao_ausente_nao_vira_aprovacao(tmp_path, monkeypatch, missing):
    # Recuperar um caso real e corromper só o registro da fronteira para conferir
    # que a validade do instrumento não depende apenas da resposta do ChatService.
    async def invalid_case(spec, failure, route, repetition, llm):
        row = await original(spec, failure, route, repetition, llm)
        if missing == "prompt":
            row["sdk"][0]["contexto_no_prompt"] = False
        elif missing == "sdk":
            row["sdk"].clear()
        else:
            row["falha"]["nlp"][0]["mesma_excecao_injetada"] = False
        row["criterios"] = executor.evaluate_case(row, spec)
        return row

    original = executor.run_case
    monkeypatch.setattr(executor, "run_case", invalid_case)
    result = executor.collect(tmp_path)
    assert not result["coleta_valida"]
    assert result["julgamento_continuidade"] == "nao_avaliado"


def test_rede_bloqueada_e_contada():
    with executor.network_blocked() as attempts:
        with pytest.raises(AssertionError, match="tentativa de rede"):
            socket.create_connection(("c03.invalid", 443))
    assert len(attempts) == 1


def test_falha_de_continuidade_nao_vira_coleta_invalida(tmp_path, monkeypatch):
    original = executor.run_case

    async def broken_recovery(spec, failure, route, repetition, llm):
        row = await original(spec, failure, route, repetition, llm)
        if route["id"] == "texto_livre":
            row["retomada"][0]["estado_depois"] = "NEW"
            row["criterios"] = executor.evaluate_case(row, spec)
        return row

    monkeypatch.setattr(executor, "run_case", broken_recovery)
    result = executor.collect(tmp_path)
    assert result["coleta_valida"]
    assert result["casos_atendidos"] == 6
    assert result["julgamento_continuidade"] == "parcialmente_atendido"
