"""C03: falhas no SDK de inferência, com NLP/ChatService reais e banco descartável."""
import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import logging
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
MARCADOR = "C03-CONTEXTO-SINTETICO"
sys.path.insert(0, str(ROOT))


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def manifest():
    files = [p for folder in ("api", "app", "data/servicos")
             for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".json", ".txt")]
    files += [HERE / "casos.json", Path(__file__), HERE / "test_executor.py",
              HERE.parent / "C03-protocolo.md"]
    return {
        "inicio_utc": now(), "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"), "git_status": git("status", "--short"),
        "python": sys.version, "executavel": sys.executable, "plataforma": platform.platform(),
        "dependencias": sorted({f"{d.metadata['Name']}=={d.version}"
                                for d in importlib.metadata.distributions()}),
        "banco": "SQLite em memoria por caso; sem DATABASE_URL",
        "credencial": "sintetica; load_dotenv neutralizado; nenhuma chamada externa",
        "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(files)},
    }


@contextmanager
def network_blocked():
    attempts = []

    def deny(*args, **kwargs):
        attempts.append({"numero": len(attempts) + 1})
        raise AssertionError("C03 bloqueou tentativa de rede")

    with patch.object(socket.socket, "connect", deny), \
            patch.object(socket.socket, "connect_ex", deny), \
            patch.object(socket, "create_connection", deny), \
            patch.object(socket, "getaddrinfo", deny):
        yield attempts


def make_error(kind):
    import httpx
    from groq import APITimeoutError, APIConnectionError, NotFoundError

    request = httpx.Request("POST", "https://c03.invalid/openai/v1/chat/completions")
    if kind == "timeout":
        return APITimeoutError(request)
    if kind == "conexao":
        return APIConnectionError(message="C03: conexao indisponivel (sintetica)", request=request)
    if kind == "modelo_indisponivel":
        body = {"error": {"message": "C03: modelo indisponivel", "code": "model_not_found"}}
        response = httpx.Response(404, request=request, json=body)
        return NotFoundError("C03: modelo indisponivel (sintetico)", response=response, body=body)
    raise ValueError(f"Falha desconhecida: {kind}")


class ObservedNLP:
    """Observa sem mudar retorno ou exceção; o NLP real continua responsável pelo RAG."""

    def __init__(self, real, injected):
        self.real = real
        self.injected = injected
        self.calls = []

    def process(self, text, user_name=None):
        record = {"consulta": text}
        self.calls.append(record)
        try:
            answer = self.real.process(text, user_name=user_name)
            record["resposta"] = answer
            return answer
        except Exception as exc:
            record.update(erro_tipo=type(exc).__name__, mesma_excecao_injetada=exc is self.injected)
            raise


async def observe_message(db, nlp, identity, text):
    from api.models.models import AuditLog, Message, User
    from api.schemas.responses import ChatResponse
    from api.services.chat_service import ChatService

    db.expire_all()
    user = db.query(User).filter_by(id_wpp=identity).one()
    before = user.state
    last_event = db.query(AuditLog.id).order_by(AuditLog.id.desc()).first()
    last_message = db.query(Message.id).order_by(Message.id.desc()).first()
    calls_before = len(nlp.calls)
    row = {"entrada": text, "estado_antes": before, "excecao_propagada": None}
    try:
        response = await ChatService(db, nlp).process_message(identity, text)
        row.update(resposta=response.text, image_url=response.image_url,
                   retorno_controlado=isinstance(response, ChatResponse) and bool(response.text.strip()))
    except Exception as exc:
        # Observação no limite do chamador: não reparar sessão nem substituir resposta.
        row.update(excecao_propagada=type(exc).__name__, retorno_controlado=False)
    db.expire_all()
    user = db.query(User).filter_by(id_wpp=identity).one()
    row.update(estado_depois=user.state, nome_depois=user.name, id_wpp_depois=user.id_wpp)
    row["nlp"] = nlp.calls[calls_before:]
    row["eventos"] = [{"tipo": e.event_type, "nivel": e.level, "mensagem": e.message,
                      "meta": e.metadata_info} for e in db.query(AuditLog).filter(
                          AuditLog.id > (last_event[0] if last_event else 0)).order_by(AuditLog.id)]
    row["mensagens_persistidas"] = [{"remetente": m.sender, "texto": m.text}
                                    for m in db.query(Message).filter(
                                        Message.id > (last_message[0] if last_message else 0)).order_by(Message.id)]
    return row


def evaluate_case(row, spec):
    """Critérios do protocolo; auditoria e redação da falha são observações separadas."""
    failure = row["falha"]
    sdk = row["sdk"]
    nlp = failure["nlp"]
    valid = (len(sdk) == 1 and sdk[0]["consulta_no_prompt"] and sdk[0]["contexto_no_prompt"]
             and sdk[0]["erro_tipo"] == row["erro_esperado"]
             and row["recuperacoes"] == [row["consulta"]] and len(nlp) == 1
             and nlp[0].get("mesma_excecao_injetada") is True
             and nlp[0].get("erro_tipo") == row["erro_esperado"])
    state_ok = failure["estado_depois"] == row["estado_inicial"]
    recovery_ok = len(row["retomada"]) == len(spec["retomada"])
    from api.services.menu_handlers import TEXTS
    for step, expected in zip(row["retomada"], spec["retomada"]):
        menu = TEXTS[expected["estado"]]["text"]
        answer = step.get("resposta", "")
        text_ok = menu in answer if expected["texto"] == "contem_menu" else menu == answer
        events = [e["tipo"] for e in step["eventos"]]
        messages_ok = step["mensagens_persistidas"] == [
            {"remetente": "user", "texto": expected["entrada"]},
            {"remetente": "bot", "texto": answer},
        ]
        step["atendida"] = (step["retorno_controlado"] and text_ok and messages_ok
                            and step["estado_depois"] == expected["estado"] and not step["nlp"]
                            and events.count("MESSAGE_SENT") == 1 and "MESSAGE_FAILED" not in events)
        recovery_ok = recovery_ok and step["atendida"]
    identity_ok = all(s["nome_depois"] == "Teste C03" and s["id_wpp_depois"] == row["id_wpp"]
                      for s in [failure, *row["retomada"]])
    return {"injecao_valida": valid, "retorno_controlado": failure["retorno_controlado"],
            "estado_preservado": state_ok and identity_ok, "continuidade_estatica": recovery_ok,
            "atendido": valid and failure["retorno_controlado"] and state_ok and identity_ok and recovery_ok}


async def run_case(spec, failure, route, repetition, llm):
    from langchain_core.documents import Document
    from langchain_core.runnables import RunnableLambda
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api.models.models import Base, Chat, User
    from api.services.nlp_service import NLPService

    error = make_error(failure["id"])
    retrievals, sdk_calls = [], []

    def retrieve(question):
        retrievals.append(question)
        return [Document(page_content=f"{MARCADOR}: documento ficticio para avaliar continuidade.")]

    def fail_sdk(**kwargs):
        prompt = "\n".join(str(m.get("content", "")) for m in kwargs.get("messages", []))
        sdk_calls.append({"erro_tipo": type(error).__name__, "consulta_no_prompt": route["consulta"] in prompt,
                          "contexto_no_prompt": MARCADOR in prompt})
        raise error

    engine = create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)
        with sessionmaker(bind=engine)() as db:
            identity = "5500000000303"
            user = User(id_wpp=identity, name="Teste C03", state=route["estado"])
            db.add(user)
            db.flush()
            db.add(Chat(user_id=user.id))
            db.commit()
            nlp = ObservedNLP(NLPService(RunnableLambda(retrieve)), error)
            row = {"id": f"R{repetition}-{failure['id']}-{route['id']}", "repeticao": repetition,
                   "tipo_falha": failure["id"], "erro_esperado": failure["classe"], "percurso": route["id"],
                   "estado_inicial": route["estado"], "consulta": route["consulta"], "id_wpp": identity}
            # A falha segue ativa durante a retomada: menus devem funcionar sem o SDK.
            with patch.object(llm.client, "create", side_effect=fail_sdk):
                row["falha"] = await observe_message(db, nlp, identity, route["entrada"])
                row["retomada"] = [await observe_message(db, nlp, identity, step["entrada"])
                                   for step in spec["retomada"]]
            row.update(sdk=sdk_calls, recuperacoes=retrievals)
            row["criterios"] = evaluate_case(row, spec)
            return row
    finally:
        engine.dispose()


def summarize(rows, expected_count, network_attempts):
    complete = len(rows) == expected_count
    valid = complete and not network_attempts and all(r["criterios"]["injecao_valida"] for r in rows)
    successes = sum(r["criterios"]["atendido"] for r in rows)
    judgment = "nao_avaliado"
    if valid:
        judgment = "atendido" if successes == expected_count else (
            "parcialmente_atendido" if successes else "nao_atendido")
    return {
        "casos_previstos": expected_count, "casos_executados": len(rows), "coleta_valida": valid,
        "tentativas_rede": network_attempts, "julgamento_continuidade": judgment,
        "casos_atendidos": successes,
        "por_percurso": {route: {
            "casos": len(group),
            **{key: sum(r["criterios"][key] for r in group) for key in (
                "retorno_controlado", "estado_preservado", "continuidade_estatica")},
            "respostas_distintas": sorted({r["falha"].get("resposta", "") for r in group}),
            "eventos_na_falha": sorted({e["tipo"] for r in group for e in r["falha"]["eventos"]}),
            "mensagens_persistidas_na_falha": [len(r["falha"]["mensagens_persistidas"]) for r in group],
            "retomadas_atendidas": sum(s["atendida"] for r in group for s in r["retomada"]),
        } for route in sorted({r["percurso"] for r in rows})
            for group in [[r for r in rows if r["percurso"] == route]]},
    }


def collect(out):
    spec = json.loads((HERE / "casos.json").read_text(encoding="utf-8"))
    rows = []
    env = {"GROQ_API_KEY": "c03-credencial-sintetica-sem-rede", "LANGCHAIN_TRACING_V2": "false",
           "LANGSMITH_TRACING": "false", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    # No Windows, criar/fechar o loop usa socketpair local. Prepará-lo antes
    # do bloqueio mantém todas as conexões da aplicação bloqueadas na coleta.
    with asyncio.Runner() as runner, network_blocked() as attempts, \
            patch.dict(os.environ, env), patch("dotenv.load_dotenv", return_value=False):
        from app.core import rag_pipeline
        with patch.object(rag_pipeline, "CACHED_LLM", None):
            llm = rag_pipeline.get_llm()
            save(out / "modelo.json", {"modelo_do_corte": rag_pipeline.MODEL_NAME,
                                      "temperatura": llm.temperature, "max_tokens": llm.max_tokens,
                                      "fronteira_injetada": "llm.client.create (SDK Groq)",
                                      "retries_http_exercitados": False, "geracao_real": False})

            async def run():
                for rep in range(1, spec["repeticoes"] + 1):
                    for failure in spec["falhas"]:
                        for route in spec["percursos"]:
                            row = await run_case(spec, failure, route, rep, llm)
                            rows.append(row)
                            save(out / "casos-executados.json", rows)
                            print(json.dumps({"caso": row["id"], **row["criterios"]}), flush=True)

            runner.run(run())
    count = spec["repeticoes"] * len(spec["falhas"]) * len(spec["percursos"])
    result = summarize(rows, count, attempts)
    save(out / "resumo.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=HERE.parent / "evidencias-c03")
    args = parser.parse_args()
    out = args.saida / f"{datetime.now():%Y%m%d-%H%M%S}-falhas-{uuid.uuid4().hex[:6]}"
    out.mkdir(parents=True, exist_ok=False)
    save(out / "ambiente.json", manifest())
    for source in (Path(__file__), HERE / "casos.json", HERE.parent / "C03-protocolo.md"):
        shutil.copyfile(source, out / source.name)
    logger = logging.getLogger("AppLogger")
    handler = logging.FileHandler(out / "aplicacao.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    previous = logger.level, logger.propagate
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    execution = {"inicio_utc": now(), "comando": sys.argv, "diretorio": str(out), "pid": os.getpid()}
    try:
        result = collect(out)
        execution.update(coleta_valida=result["coleta_valida"],
                         julgamento_continuidade=result["julgamento_continuidade"])
    except Exception as exc:
        logger.exception("Impedimento do instrumento C03")
        execution.update(coleta_valida=False, erro_tipo=type(exc).__name__)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous[0])
        logger.propagate = previous[1]
        handler.close()
    execution["fim_utc"] = now()
    save(out / "execucao.json", execution)
    print(json.dumps({"lote": str(out), **execution}, ensure_ascii=False))
    return 0 if execution["coleta_valida"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
