"""C04: processo isolado, casos RAG reais, evidências e cobertura por pacote."""
import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHE_NAMES = ("HF_HOME", "HF_HUB_CACHE", "SENTENCE_TRANSFORMERS_HOME", "TORCH_HOME", "XDG_CACHE_HOME")
ESSENTIAL_ENV = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "TEMP", "TMP",
                 "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE"}
CREDENTIAL_NAMES = ("GROQ_API_KEY", "OPENAI_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN",
                    "LANGSMITH_API_KEY", "LANGCHAIN_API_KEY", "DATABASE_URL")


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def manifest():
    paths = [p for folder in ("api", "app", "data/servicos", "tests")
             for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".json", ".txt")]
    paths += list(HERE.glob("*.py")) + [HERE / "casos.json", HERE.parent / "C04-protocolo.md",
                                       ROOT / "pyproject.toml", ROOT / ".github/workflows/ci.yml"]
    return {"inicio_utc": now(), "commit": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"), "git_status": git("status", "--short"),
            "python": sys.version, "plataforma": platform.platform(),
            "dependencias": sorted({f"{d.metadata['Name']}=={d.version}"
                                    for d in importlib.metadata.distributions()}),
            "sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(paths))}}


def isolated_environment(out):
    env = {k: v for k, v in os.environ.items() if k.upper() in ESSENTIAL_ENV}
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1",
               PYTHONPATH=str(ROOT), PYTHON_DOTENV_DISABLED="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               LANGCHAIN_TRACING_V2="false", LANGSMITH_TRACING="false", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
               HF_HUB_DISABLE_IMPLICIT_TOKEN="1", DO_NOT_TRACK="1", C04_WORKER="1")
    for name in CACHE_NAMES:
        path = out / "cache-vazio" / name.lower()
        path.mkdir(parents=True, exist_ok=False)
        env[name] = str(path)
    return env


@contextmanager
def external_access_blocked():
    attempts = []

    def deny(kind):
        def fail(*args, **kwargs):
            attempts.append({"tipo": kind, "numero": len(attempts) + 1})
            raise RuntimeError(f"C04 bloqueou acesso externo: {kind}")
        return fail

    with ExitStack() as stack:
        for owner, name, kind in (
            (socket.socket, "connect", "socket_connect"),
            (socket.socket, "connect_ex", "socket_connect_ex"),
            (socket.socket, "sendto", "socket_sendto"),
            (socket, "create_connection", "create_connection"),
            (socket, "getaddrinfo", "dns_getaddrinfo"),
            (socket, "gethostbyname", "dns_gethostbyname"),
            (socket, "gethostbyname_ex", "dns_gethostbyname_ex"),
            (socket, "gethostbyaddr", "dns_gethostbyaddr"),
            (subprocess, "Popen", "subprocess"),
            (os, "system", "os_system"),
        ):
            stack.enter_context(patch.object(owner, name, side_effect=deny(kind)))
        yield attempts


def cache_inventory():
    return {name: [{"arquivo": p.relative_to(Path(os.environ[name])).as_posix(),
                    "bytes": p.stat().st_size, "sha256": digest(p)}
                   for p in sorted(Path(os.environ[name]).rglob("*")) if p.is_file()]
            for name in CACHE_NAMES}


def make_corpus(out, spec):
    root = out / "projeto-sintetico"
    folder = root / "data/servicos"
    folder.mkdir(parents=True)
    (root / "app/core").mkdir(parents=True)
    corpus = spec["corpus"]
    for service in corpus["servicos"]:
        marker = corpus["marcador"].format(servico=service.upper())
        text = "\n\n".join(corpus["paragrafo"].format(marcador=marker, servico=service, numero=n)
                             for n in range(1, corpus["paragrafos_por_documento"] + 1))
        (folder / f"{service.lower()}.txt").write_text(text + "\n", encoding="utf-8")
    (folder / "ignorar.md").write_text("C04: este arquivo não deve ser ingerido.\n", encoding="utf-8")
    return root


class EvidencePlugin:
    def __init__(self, out, spec):
        self.out = out
        self.spec = spec
        self.rows = {}

    def pytest_configure(self, config):
        config.c04_out = self.out
        config.c04_observations = self.rows

    def pytest_runtest_logreport(self, report):
        case_id = report.nodeid.rsplit("::", 1)[-1].split("_")[1]
        row = self.rows.setdefault(case_id, {"id": case_id})
        row.setdefault("pytest", []).append({"fase": report.when, "resultado": report.outcome})
        if report.failed:
            row["falha_teste"] = str(report.longrepr)
        save(self.out / "casos-executados.json", list(self.rows.values()))


def coverage_summary(data):
    packages = {}
    for package in ("app", "api"):
        files = {name: value["summary"] for name, value in data["files"].items()
                 if name.replace("\\", "/").startswith(package + "/")}
        fields = ("num_statements", "covered_lines", "missing_lines", "num_branches", "covered_branches")
        totals = {key: sum(f[key] for f in files.values()) for key in fields}
        totals["percentual_linhas"] = round(100 * totals["covered_lines"] / totals["num_statements"], 2)
        totals["percentual_ramos"] = (round(100 * totals["covered_branches"] / totals["num_branches"], 2)
                                       if totals["num_branches"] else None)
        packages[package] = {"totais": totals, "arquivos": files}
    return packages


def summarize(spec, rows, isolation, hashes_ok, coverage_exists, pytest_code):
    expected = [c["id"] for c in spec["casos"]]
    observed = [r["id"] for r in rows]
    complete = len(observed) == len(expected) and set(observed) == set(expected)
    complete = complete and all(any(p["fase"] == "call" for p in r.get("pytest", [])) for r in rows)
    isolation_ok = (isolation.get("bloqueio_ativo") and not isolation.get("tentativas", [True])
                    and not isolation.get("credenciais_presentes", [True])
                    and not any(isolation.get("cache_antes", {"erro": [True]}).values())
                    and not any(isolation.get("cache_depois", {"erro": [True]}).values())
                    and isolation.get("dotenv_neutralizado") is True)
    valid = bool(complete and isolation_ok and hashes_ok and coverage_exists and pytest_code in (0, 1))
    successes = sum(all(p["resultado"] == "passed" for p in r.get("pytest", []))
                    and bool(r.get("observacoes")) for r in rows)
    # Ausência de observações é falha do instrumento, não evidência da arquitetura.
    valid = valid and all(bool(r.get("observacoes")) for r in rows)
    judgment = "nao_avaliado"
    if valid:
        judgment = "atendido" if successes == len(expected) else (
            "parcialmente_atendido" if successes else "nao_atendido")
    return {"casos_previstos": len(expected), "casos_executados": len(rows),
            "casos_aprovados": successes, "matriz_completa": complete,
            "isolamento_valido": bool(isolation_ok), "hashes_preservados": hashes_ok,
            "cobertura_produzida": coverage_exists, "coleta_valida": bool(valid),
            "julgamento": judgment, "pytest_exit_code": pytest_code}


def worker(out):
    sys.path.insert(0, str(ROOT))
    spec = load(out / "casos.json")
    make_corpus(out, spec)
    isolation = {"inicio_utc": now(), "ambiente_por_lista_permitida": True,
                 "nomes_variaveis": sorted(os.environ),
                 "credenciais_presentes": [k for k in CREDENTIAL_NAMES if os.environ.get(k)],
                 "cache_antes": cache_inventory(), "bloqueio_ativo": False}
    save(out / "isolamento.json", isolation)
    with external_access_blocked() as attempts, patch("dotenv.load_dotenv", return_value=False) as dotenv:
        isolation.update(bloqueio_ativo=True, dotenv_neutralizado=True)
        import coverage
        import pytest

        cov = coverage.Coverage(config_file=False, data_file=str(out / ".coverage"), branch=True,
                                source=[str(ROOT / "app"), str(ROOT / "api")], omit=[str(ROOT / "api/alembic/*")])
        plugin = EvidencePlugin(out, spec)
        cov.start()
        try:
            code = int(pytest.main([str(HERE / "test_cenario.py"), "-q", "-p", "no:cacheprovider",
                                    "--basetemp", str(out / "temporarios")], plugins=[plugin]))
        finally:
            cov.stop()
            cov.save()
            cov.json_report(outfile=str(out / "cobertura.json"), pretty_print=True)
            with (out / "cobertura.txt").open("w", encoding="utf-8") as stream:
                cov.report(file=stream, show_missing=True)
            save(out / "cobertura-por-pacote.json", coverage_summary(load(out / "cobertura.json")))
            isolation.update(tentativas=attempts, cache_depois=cache_inventory(),
                             chamadas_dotenv_suprimidas=dotenv.call_count, fim_utc=now())
            save(out / "isolamento.json", isolation)
            save(out / "casos-executados.json", list(plugin.rows.values()))
    return code


def collect(out):
    out.mkdir(parents=True, exist_ok=False)
    env_manifest = manifest()
    save(out / "ambiente.json", env_manifest)
    for source in [*HERE.glob("*.py"), HERE / "casos.json", HERE.parent / "C04-protocolo.md"]:
        shutil.copyfile(source, out / source.name)
    child_env = isolated_environment(out)
    execution = {"inicio_utc": now(), "comando": sys.argv, "pid_pai": os.getpid()}
    code = None
    try:
        with (out / "pytest.txt").open("w", encoding="utf-8") as stream:
            child = subprocess.run([sys.executable, str(HERE / "executar.py"), "--worker", str(out)],
                                   cwd=ROOT, env=child_env, stdout=stream, stderr=subprocess.STDOUT,
                                   timeout=240, check=False,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        code = child.returncode
    except Exception as exc:
        execution["erro_tipo"] = type(exc).__name__
    hashes_ok = all((ROOT / name).is_file() and digest(ROOT / name) == value
                    for name, value in env_manifest["sha256"].items())
    rows = load(out / "casos-executados.json") if (out / "casos-executados.json").exists() else []
    isolation = load(out / "isolamento.json") if (out / "isolamento.json").exists() else {}
    result = summarize(load(out / "casos.json"), rows, isolation, hashes_ok,
                       (out / "cobertura-por-pacote.json").exists(), code)
    save(out / "resumo.json", result)
    execution.update(fim_utc=now(), **result)
    save(out / "execucao.json", execution)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=HERE.parent / "evidencias-c04")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker.resolve())
    out = args.saida.resolve() / f"{datetime.now():%Y%m%d-%H%M%S}-offline-{uuid.uuid4().hex[:6]}"
    result = collect(out)
    print(json.dumps({"lote": str(out), **result}, ensure_ascii=False))
    return 0 if result["coleta_valida"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
