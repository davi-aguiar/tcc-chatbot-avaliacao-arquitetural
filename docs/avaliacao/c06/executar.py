"""C06: preparação e captura local do fluxo, sem chave real ou envio externo."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import importlib.util
import json
import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def now():
    return datetime.now(UTC).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schedule(spec):
    return [(r, c) for r in range(1, spec["repeticoes"] + 1) for c in spec["casos"]]


def validate(spec):
    assert spec["cenario"] == "C06" and spec["repeticoes"] == 2
    assert [c["id"] for c in spec["casos"]] == [f"D{i:02d}" for i in range(1, 8)]
    assert [c["http_status"] for c in spec["casos"]] == [200, 400, 200, 400, 200, 400, None]
    fixture = spec["fixture"]
    markers = [fixture[k] for k in ("id_cadastrado", "nome_cadastrado", "id_declarado",
                                   "nome_declarado", "historico_usuario", "historico_bot")]
    assert len(set(markers)) == len(markers)
    assert all(marker not in fixture["contexto"] for marker in markers)
    menu = load(ROOT / "api/services/menu_texts.json")
    for case in spec["casos"]:
        if case["percurso"] == "menu":
            assert menu[case["estado"]]["options"][case["entrada"]]["query"] == case["consulta_esperada"]
        if case["percurso"] == "autodeclarado":
            assert fixture["nome_declarado"] in case["entrada"] and fixture["id_declarado"] in case["entrada"]
        assert fixture["nome_cadastrado"] not in case["entrada"]
        assert fixture["id_cadastrado"] not in case["entrada"]


def locations(value, marker, path="$", result=None):
    result = [] if result is None else result
    if isinstance(value, dict):
        for key, item in value.items():
            locations(item, marker, f"{path}.{key}", result)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            locations(item, marker, f"{path}[{index}]", result)
    elif isinstance(value, str) and marker in value:
        result.append(path)
    return result


def redact(value, secret):
    if isinstance(value, dict):
        return {k: redact(v, secret) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secret) for v in value]
    return value.replace(secret, "[CREDENCIAL_SINTETICA_OMITIDA]") if isinstance(value, str) else value


@contextmanager
def no_network():
    attempts = []

    def deny(*args, **kwargs):
        attempts.append({"numero": len(attempts) + 1})
        raise RuntimeError("C06 bloqueou uma operação externa")

    with patch.object(socket.socket, "connect", deny), patch.object(socket.socket, "connect_ex", deny), \
            patch.object(socket.socket, "sendto", deny), patch.object(socket, "getaddrinfo", deny), \
            patch.object(socket, "create_connection", deny), patch.object(subprocess, "Popen", deny), \
            patch.object(os, "system", deny):
        yield attempts


@contextmanager
def clean_environment(secret):
    allowed = {k: v for k, v in os.environ.items() if k.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
        "PROGRAMDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "COMSPEC", "PATHEXT"}}
    allowed.update(GROQ_API_KEY=secret, PYTHON_DOTENV_DISABLED="1", HF_HUB_OFFLINE="1",
                   HF_HUB_DISABLE_TELEMETRY="1", LANGSMITH_TRACING="false", LANGCHAIN_TRACING="false",
                   LANGCHAIN_TRACING_V2="false", LANGCHAIN_CALLBACKS_BACKGROUND="false")
    with patch.dict(os.environ, allowed, clear=True), patch("dotenv.load_dotenv", return_value=False):
        yield


@contextmanager
def capture_logs():
    rows = []

    class Capture(logging.Handler):
        def emit(self, record):
            rows.append({"logger": record.name, "nivel": record.levelname,
                         "mensagem": record.getMessage(), "formatado": self.format(record)})

    root_logger = logging.getLogger()
    app_logger = logging.getLogger("AppLogger")
    with patch.object(root_logger, "handlers", [Capture()]), patch.object(root_logger, "level", logging.INFO), \
            patch.object(app_logger, "handlers", []), patch.object(app_logger, "propagate", True), \
            patch.object(app_logger, "level", logging.NOTSET):
        yield rows


def snapshot(db):
    from api.models.models import AuditLog, Chat, Message, User

    db.expire_all()
    return {
        "users": [{"id": u.id, "id_wpp": u.id_wpp, "name": u.name, "state": u.state}
                  for u in db.query(User).order_by(User.id)],
        "chats": [{"id": c.id, "user_id": c.user_id} for c in db.query(Chat).order_by(Chat.id)],
        "messages": [{"id": m.id, "chat_id": m.chat_id, "sender": m.sender, "text": m.text}
                     for m in db.query(Message).order_by(Message.id)],
        "audit_logs": [{"id": e.id, "user_id": e.user_id, "event_type": e.event_type,
                        "level": e.level, "message": e.message, "metadata_info": e.metadata_info}
                       for e in db.query(AuditLog).order_by(AuditLog.id)]}


def diagnostics(row, case, fixture):
    regions = {"payload": [r["corpo"] for r in row["http"]], "logs": row["logs"],
               "persistencia": row["depois"]}
    markers = {k: fixture[k] for k in ("id_cadastrado", "nome_cadastrado", "id_declarado",
                                      "nome_declarado", "historico_usuario", "historico_bot", "contexto")}
    markers["consulta"] = case.get("consulta_esperada", case["entrada"])
    markers["relato"] = "RELATO_C06_FICTICIO"
    return {region: {name: locations(value, marker) for name, marker in markers.items()}
            for region, value in regions.items()}


def observe(case, fixture, round_number):
    """Observação isolada; não escreve artefatos nem atribui julgamento final."""
    secret = "c06-" + uuid.uuid4().hex
    row = {"id": f"{case['id']}-R{round_number}", "inicio_utc": now(), "caso": case["id"],
           "rodada": round_number, "entrada": case["entrada"], "fixture": fixture,
           "http": [], "nlp": [], "recuperacoes": [], "erro_instrumento": None}
    loop = asyncio.new_event_loop()
    try:
        with clean_environment(secret), capture_logs() as logs, no_network() as attempts:
            import httpx
            from langchain_core.documents import Document
            from langchain_core.runnables import RunnableLambda
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from api.models.models import Base, Chat, Message, User
            from api.services.chat_service import ChatService
            from api.services.nlp_service import NLPService
            from app.core import rag_pipeline

            def transport(request):
                row["http"].append({"metodo": request.method, "url": str(request.url.copy_with(query=None)),
                                    "autenticacao_presente": "authorization" in request.headers,
                                    "corpo": json.loads(request.content), "status_sintetico": case["http_status"]})
                if case["http_status"] == 400:
                    return httpx.Response(400, json={"error": {"message": "ERRO_C06_SINTETICO",
                        "type": "invalid_request_error", "code": "c06_sintetico"}})
                return httpx.Response(200, json={"id": "c06-local", "object": "chat.completion", "created": 0,
                    "model": rag_pipeline.MODEL_NAME, "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": fixture["resposta_sintetica"]}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})

            def retrieve(question):
                row["recuperacoes"].append(question)
                return [Document(page_content=fixture["contexto"], metadata={"source": "c06-documento-sintetico.txt"})]

            class ObservedNLP:
                def __init__(self):
                    self.real = NLPService(RunnableLambda(retrieve))

                def process(self, text, user_name=None):
                    record = {"consulta": text, "user_name_recebido": user_name, "erro_tipo": None}
                    row["nlp"].append(record)
                    try:
                        answer = self.real.process(text, user_name=user_name)
                        record["resposta"] = answer
                        return answer
                    except Exception as exc:
                        record["erro_tipo"] = type(exc).__name__
                        raise

            engine = create_engine("sqlite://")
            original_factory = rag_pipeline.ChatGroq
            try:
                Base.metadata.create_all(engine)
                with sessionmaker(bind=engine)() as db, httpx.Client(
                        transport=httpx.MockTransport(transport), trust_env=False) as client:
                    user = User(id_wpp=fixture["id_cadastrado"], name=fixture["nome_cadastrado"], state=case["estado"])
                    db.add(user)
                    db.flush()
                    chat = Chat(user=user)
                    db.add(chat)
                    db.flush()
                    db.add_all([Message(chat=chat, sender="user", text=fixture["historico_usuario"]),
                                Message(chat=chat, sender="bot", text=fixture["historico_bot"])])
                    db.commit()
                    row["antes"] = snapshot(db)

                    def make_client(**kwargs):
                        return original_factory(**kwargs, http_client=client)

                    with patch.object(rag_pipeline, "CACHED_LLM", None), patch.object(rag_pipeline, "ChatGroq", make_client):
                        answer = loop.run_until_complete(ChatService(db, ObservedNLP()).process_message(
                            fixture["id_cadastrado"], case["entrada"]))
                    row["resposta_chamador"] = {"text": answer.text, "image_url": answer.image_url}
                    row["depois"] = snapshot(db)
            finally:
                engine.dispose()
            row["logs"] = list(logs)
            row["tentativas_externas"] = list(attempts)
    except Exception as exc:  # noqa: BLE001 - fronteira do instrumento: invalidar e registrar só o tipo.
        row["erro_instrumento"] = type(exc).__name__
    finally:
        loop.close()
    if row["erro_instrumento"] is None:
        row["localizacoes"] = diagnostics(row, case, fixture)
        row["credencial_em_dados_brutos"] = locations(
            {"http": row["http"], "logs": row["logs"], "banco": row["depois"]}, secret)
    row["fim_utc"] = now()
    row["observacao_valida"] = (row["erro_instrumento"] is None and not row.get("tentativas_externas", [])
        and len(row["http"]) == len(row["nlp"]) == len(row["recuperacoes"]) == case["chamadas_previstas"]
        and all(r["status_sintetico"] == case["http_status"] for r in row["http"]))
    return redact(row, secret)


def source_files():
    files = [p for folder in ("app", "api", "data/servicos") for p in (ROOT / folder).rglob("*")
             if p.is_file() and p.suffix in (".py", ".json", ".txt") and "__pycache__" not in p.parts]
    return sorted(set(files + list(HERE.glob("*.py")) + [HERE / "casos.json", HERE.parent / "C06-protocolo.md"]))


def run(args):
    spec = load(HERE / "casos.json")
    validate(spec)
    out = args.saida / f"{datetime.now():%Y%m%d-%H%M%S}-{args.modo}-{uuid.uuid4().hex[:6]}"
    out.mkdir(parents=True, exist_ok=False)
    files = source_files()
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    metadata = {"data_utc": now(), "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip(),
                "python": sys.version, "plataforma": platform.platform(), "modo": args.modo, "sha256": hashes,
                "dependencias": sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
                "credencial_real_lida": False, "dotenv_lido": False}
    save(out / "ambiente.json", metadata)
    deps = {name: importlib.util.find_spec(name) is not None for name in (
        "dotenv", "httpx", "groq", "sqlalchemy", "langchain_core", "langchain_groq", "pytest")}
    status = {"modo": args.modo, "inicio_utc": now(), "matriz_valida": True, "dependencias": deps,
              "observacoes_previstas": len(schedule(spec)), "observacoes_executadas": 0,
              "coleta_completa": False, "julgamento": "nao_avaliado", "erro_tipo": None}
    try:
        if not all(deps.values()):
            raise RuntimeError("Dependência ausente")
        if args.modo == "coletar":
            for p in files:
                target = out / "fontes" / p.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
            rows = []
            for repetition, case in schedule(spec):
                row = observe(case, spec["fixture"], repetition)
                save(out / f"{row['id']}.json", row)
                rows.append(row)
                status["observacoes_executadas"] = len(rows)
            status["coleta_completa"] = len(rows) == 14 and all(r["observacao_valida"] for r in rows)
            status["julgamento"] = "pendente_analise" if status["coleta_completa"] else "nao_avaliado_integralmente"
        else:
            status["preparacao_completa"] = True
    except Exception as exc:  # noqa: BLE001 - preservar lote impedido sem persistir mensagens de exceção.
        status["erro_tipo"] = type(exc).__name__
    status["fontes_inalteradas"] = all(sha(ROOT / p) == expected for p, expected in hashes.items())
    status["fim_utc"] = now()
    save(out / "execucao.json", status)
    print(json.dumps({"lote": str(out), **status}, ensure_ascii=False))
    complete = status.get("preparacao_completa", False) if args.modo == "preparar" else status["coleta_completa"]
    return 0 if complete and status["fontes_inalteradas"] and not status["erro_tipo"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("preparar", "coletar"))
    parser.add_argument("--saida", type=Path, default=HERE.parent / "evidencias-c06")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
