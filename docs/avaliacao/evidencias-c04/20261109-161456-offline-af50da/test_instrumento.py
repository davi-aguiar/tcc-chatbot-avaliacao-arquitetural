"""Verificações do instrumento, separadas dos 16 casos arquiteturais."""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import socket
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location("executor_c04", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


@pytest.mark.parametrize("operation", ["dns", "connect", "udp", "subprocess", "system"])
def test_bloqueio_detecta_acesso_mesmo_sem_rede_real(operation):
    with executor.external_access_blocked() as attempts:
        with pytest.raises(RuntimeError, match="C04 bloqueou acesso externo"):
            if operation == "dns":
                socket.getaddrinfo("c04.invalid", 443)
            elif operation == "connect":
                with socket.socket() as sock:
                    sock.connect(("127.0.0.1", 9))
            elif operation == "udp":
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(b"c04", ("127.0.0.1", 9))
            elif operation == "subprocess":
                subprocess.Popen(["c04-programa-inexistente"])
            else:
                os.system("c04-programa-inexistente")
    assert len(attempts) == 1


def test_ambiente_nao_herda_credenciais_cache_ou_modelo(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "c04-chave-sintetica")
    monkeypatch.setenv("HF_TOKEN", "c04-token-sintetico")
    monkeypatch.setenv("EMBEDDINGS_MODEL", "c04-modelo-herdado")
    monkeypatch.setenv("DATABASE_URL", "c04-banco-herdado")
    env = executor.isolated_environment(tmp_path)
    assert not any(name in env for name in (*executor.CREDENTIAL_NAMES, "EMBEDDINGS_MODEL"))
    assert env["PYTHON_DOTENV_DISABLED"] == env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert all(Path(env[k]).is_relative_to(tmp_path) and not list(Path(env[k]).iterdir())
               for k in executor.CACHE_NAMES)


@pytest.fixture(scope="module")
def preflight(tmp_path_factory):
    out = tmp_path_factory.mktemp("c04-instrumento") / "lote"
    result = executor.collect(out)
    assert result["coleta_valida"], (out / "pytest.txt").read_text(encoding="utf-8")
    return out, result


def test_ciclo_completo_em_subprocesso_e_cobertura(preflight):
    out, result = preflight
    assert result["julgamento"] == "atendido" and result["casos_aprovados"] == 16
    isolation = executor.load(out / "isolamento.json")
    assert isolation["tentativas"] == [] and isolation["credenciais_presentes"] == []
    assert not any(isolation["cache_antes"].values()) and not any(isolation["cache_depois"].values())
    coverage = executor.load(out / "cobertura-por-pacote.json")
    for package in ("app", "api"):
        assert coverage[package]["totais"]["num_statements"] > 0
        assert coverage[package]["totais"]["covered_lines"] > 0
    files = {name.replace("\\", "/"): value for name, value in executor.load(out / "cobertura.json")["files"].items()}
    assert files["app/core/rag_pipeline.py"]["summary"]["covered_lines"] > 20
    assert files["api/services/nlp_service.py"]["summary"]["covered_lines"] > 20
    assert (out / "projeto-sintetico/data/servicos/aurora.txt").exists()


@pytest.mark.parametrize("corruption", ["rede", "matriz", "observacao", "fontes", "cobertura"])
def test_instrumento_invalido_nao_vira_aprovacao(preflight, corruption):
    out, _ = preflight
    spec = executor.load(out / "casos.json")
    rows = deepcopy(executor.load(out / "casos-executados.json"))
    isolation = deepcopy(executor.load(out / "isolamento.json"))
    if corruption == "rede":
        isolation["tentativas"] = [{"tipo": "dns"}]
    elif corruption == "matriz":
        rows.pop()
    elif corruption == "observacao":
        rows[0]["observacoes"] = {}
    result = executor.summarize(spec, rows, isolation, corruption != "fontes", corruption != "cobertura", 0)
    assert not result["coleta_valida"] and result["julgamento"] == "nao_avaliado"


def test_falha_de_caso_e_resultado_parcial_nao_impedimento(preflight):
    out, _ = preflight
    rows = deepcopy(executor.load(out / "casos-executados.json"))
    next(p for p in rows[0]["pytest"] if p["fase"] == "call")["resultado"] = "failed"
    result = executor.summarize(executor.load(out / "casos.json"), rows,
                                executor.load(out / "isolamento.json"), True, True, 1)
    assert result["coleta_valida"] and result["julgamento"] == "parcialmente_atendido"
    assert result["casos_aprovados"] == 15
