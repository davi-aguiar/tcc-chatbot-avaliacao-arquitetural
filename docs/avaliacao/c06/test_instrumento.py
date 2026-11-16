"""Verificações do instrumento C06; não integram a amostra de 14 observações."""
import importlib.util
import json
import os
import socket
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("executor_c06", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


def matrix():
    return executor.load(executor.HERE / "casos.json")


def test_matriz_ordem_e_query_real():
    spec = matrix()
    executor.validate(spec)
    assert [(r, c["id"]) for r, c in executor.schedule(spec)] == [
        (r, f"D{i:02d}") for r in (1, 2) for i in range(1, 8)]


def test_rejeita_matriz_com_identidade_no_contexto():
    spec = matrix()
    spec["fixture"]["contexto"] += spec["fixture"]["nome_cadastrado"]
    with pytest.raises(AssertionError):
        executor.validate(spec)


def test_rejeita_query_diferente_do_menu():
    spec = matrix()
    spec["casos"][0]["consulta_esperada"] = "CONSULTA_INEXISTENTE"
    with pytest.raises(AssertionError):
        executor.validate(spec)


@pytest.mark.parametrize("operation", ["dns", "connect", "udp", "process"])
def test_bloqueio_conta_tentativa(operation):
    with executor.no_network() as attempts, pytest.raises(RuntimeError):
        if operation == "dns":
            socket.getaddrinfo("c06.invalid", 443)
        elif operation == "connect":
            with socket.socket() as sock:
                sock.connect(("127.0.0.1", 9))
        elif operation == "udp":
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(b"c06", ("127.0.0.1", 9))
        else:
            subprocess.Popen(["c06-programa-inexistente"])
    assert attempts == [{"numero": 1}]


def test_localizacao_antes_de_omitir_valor_secreto():
    value = {"logs": [{"text": "prefixo SEGREDO_TESTE_C06 sufixo"}], "normal": "outro"}
    assert executor.locations(value, "SEGREDO_TESTE_C06") == ["$.logs[0].text"]
    cleaned = executor.redact(value, "SEGREDO_TESTE_C06")
    assert "SEGREDO_TESTE_C06" not in json.dumps(cleaned)
    assert cleaned["normal"] == "outro"


def test_ambiente_nao_herda_credenciais_e_restaura(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "CHAVE_HERDADA_TESTE_C06")
    monkeypatch.setenv("C06_TOKEN_HERDADO", "OUTRO_SEGREDO_C06")
    with executor.clean_environment("CREDENCIAL_CONTROLADA_C06"):
        assert os.environ["GROQ_API_KEY"] == "CREDENCIAL_CONTROLADA_C06"
        assert "C06_TOKEN_HERDADO" not in os.environ
        assert os.environ["PYTHON_DOTENV_DISABLED"] == "1"
    assert os.environ["GROQ_API_KEY"] == "CHAVE_HERDADA_TESTE_C06"


@pytest.mark.parametrize("index", [0, 3, 6])
def test_registro_com_sdk_e_aplicacao_reais_sem_rede(index):
    spec = matrix()
    case = deepcopy(spec["casos"][index])
    case["id"] = f"INSTRUMENTO-{index}"
    row = executor.observe(case, spec["fixture"], 0)
    assert row["observacao_valida"], row.get("erro_instrumento")
    assert row["tentativas_externas"] == []
    assert len(row["antes"]["messages"]) == 2
    assert set(row["depois"]) == {"users", "chats", "messages", "audit_logs"}
    assert row["logs"]
    if case["chamadas_previstas"]:
        request, = row["http"]
        assert request["metodo"] == "POST" and request["autenticacao_presente"]
        assert set(request) == {"metodo", "url", "autenticacao_presente", "corpo", "status_sintetico"}
        body = json.dumps(request["corpo"], ensure_ascii=False)
        assert case.get("consulta_esperada", case["entrada"]) in body
        assert spec["fixture"]["contexto"] in body
        assert row["localizacoes"]["payload"]["contexto"]
        assert bool(row["nlp"][0]["erro_tipo"]) == (case["http_status"] == 400)
    else:
        assert row["http"] == row["nlp"] == row["recuperacoes"] == []


def test_preparacao_nao_executa_observacoes(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Preparação não pode executar a amostra")
    monkeypatch.setattr(executor, "observe", forbidden)
    assert executor.run(SimpleNamespace(modo="preparar", saida=tmp_path)) == 0
    batch, = tmp_path.iterdir()
    status = executor.load(batch / "execucao.json")
    assert status["preparacao_completa"] and status["observacoes_previstas"] == 14
    assert status["observacoes_executadas"] == 0 and status["coleta_completa"] is False
    assert status["julgamento"] == "nao_avaliado"
