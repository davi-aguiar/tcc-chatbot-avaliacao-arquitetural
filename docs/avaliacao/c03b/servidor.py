"""Servidor isolado C03-B. Somente loopback; aplicação funcional importada sem edição."""
import asyncio
from contextlib import asynccontextmanager
import contextvars
import json
import logging
import os
from pathlib import Path
import socket
import sys
import threading
import time
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
REQUEST_ID = contextvars.ContextVar("c03b_request", default="preparacao")
RATE_HEADERS = ("retry-after", "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
                "x-ratelimit-reset-tokens", "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests")


def main():
    import httpx
    import uvicorn
    from dotenv import dotenv_values
    from langchain_core.documents import Document
    from langchain_core.runnables import RunnableLambda
    from langchain_groq import ChatGroq

    out = Path(sys.argv[1]).resolve()
    config = json.loads((out / "config.json").read_text(encoding="utf-8"))
    mode = config["modo"]
    key = (dotenv_values(ROOT / ".env").get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")) if mode == "real" else "c03b-chave-sintetica"
    if not key:
        raise RuntimeError("Credencial ausente para serie real")
    os.environ.update(DATABASE_URL="sqlite:///" + (out / "descartavel.db").as_posix(),
                      WEBHOOK_TOKEN="c03b-token-sintetico", GROQ_API_KEY=key,
                      LANGSMITH_TRACING="false", LANGCHAIN_TRACING_V2="false",
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    if mode == "real":
        os.environ["EMBEDDINGS_MODEL"] = config["embeddings_snapshot"]
    autoenv = patch("dotenv.load_dotenv", return_value=False)
    autoenv.start()
    lock = threading.Lock()
    events_file = (out / "eventos.jsonl").open("w", encoding="utf-8", buffering=1)

    def emit(event, **values):
        with lock:
            events_file.write(json.dumps({"evento": event, "t": time.perf_counter(),
                                          "rid": REQUEST_ID.get(), **values}, ensure_ascii=False) + "\n")

    if mode == "controlado":
        connect = socket.socket.connect
        connect_ex = socket.socket.connect_ex

        def guard(original):
            def guarded(sock, address):
                if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "::1"):
                    emit("rede_externa_bloqueada")
                    raise AssertionError("C03B: conexao externa bloqueada")
                return original(sock, address)
            return guarded

        patch.object(socket.socket, "connect", guard(connect)).start()
        patch.object(socket.socket, "connect_ex", guard(connect_ex)).start()
        fake_boot = ModuleType("app.main")
        fake_boot.setup_system = lambda: {"servicos": RunnableLambda(
            lambda question: [Document(page_content="C03B-CONTEXTO-SINTETICO: ensaio de concorrencia.")])}
        sys.modules["app.main"] = fake_boot

    active = {"perfil": "estatico", "atraso_s": config["atraso_s"], "usuarios": []}
    attempts = {}

    class ProviderTransport(httpx.BaseTransport):
        def __init__(self):
            self.real = httpx.HTTPTransport() if mode == "real" else None

        def handle_request(self, request):
            rid = REQUEST_ID.get()
            attempts[rid] = attempts.get(rid, 0) + 1
            emit("provedor_inicio", tentativa=attempts[rid])
            response = None
            try:
                if self.real:
                    response = self.real.handle_request(request)
                elif active["perfil"] == "limite_429" and attempts[rid] == 1:
                    response = httpx.Response(429, request=request, headers={"retry-after": "0.5"},
                                              json={"error": {"message": "C03B quota sintetica", "type": "rate_limit_error"}})
                else:
                    if active["perfil"] in ("rag_lento", "timeout_cliente"):
                        time.sleep(active["atraso_s"])
                    response = httpx.Response(200, request=request, json={
                        "id": "c03b-sintetico", "object": "chat.completion", "created": 0,
                        "model": config["modelo"], "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "C03B: resposta sintetica de continuidade."}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}})
                emit("provedor_resposta", status=response.status_code,
                     cabecalhos={k: response.headers[k] for k in RATE_HEADERS if k in response.headers})
                return response
            except Exception as exc:
                emit("provedor_erro", tipo=type(exc).__name__)
                raise
            finally:
                emit("provedor_fim")

        def close(self):
            if self.real:
                self.real.close()

    transport_client = httpx.Client(transport=ProviderTransport(), timeout=35)
    from app.core import rag_pipeline
    rag_pipeline.CACHED_LLM = ChatGroq(model=config["modelo"], temperature=0.1, max_tokens=500,
                                      max_retries=2, timeout=35, api_key=key, http_client=transport_client)
    boot_start = time.perf_counter()
    from api.main import app
    from api.db.database import engine, SessionLocal
    from api.models.models import Base, User, Chat, Message, AuditLog
    import api.routes.webhook as webhook
    from fastapi import Request
    Base.metadata.create_all(engine)
    boot = {"montagem_aplicacao_s": time.perf_counter() - boot_start, "modo": mode}
    if mode == "real":
        from app.main import METRICAS_INDEXACAO
        boot["metricas_indexacao"] = dict(METRICAS_INDEXACAO)
    (out / "boot.json").write_text(json.dumps(boot, indent=2), encoding="utf-8")

    class ObservedNLP:
        def __init__(self, real):
            self.real = real

        def process(self, text, user_name=None):
            emit("nlp_inicio")
            try:
                return self.real.process(text, user_name=user_name)
            except Exception as exc:
                emit("nlp_erro", tipo=type(exc).__name__)
                raise
            finally:
                emit("nlp_fim")

    app.state.nlp_service = ObservedNLP(app.state.nlp_service)

    # Preserva send_text/send_image reais; intercepta somente o transporte final.
    def gateway_post(url, **kwargs):
        emit("envio_inicio")
        if active["perfil"] == "envio_lento":
            time.sleep(active["atraso_s"])
        payload = kwargs["json"]
        emit("envio_fim", texto=payload.get("text", payload.get("caption", "")), numero=payload["number"])
        import requests
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        return response

    patch.object(webhook.requests, "post", side_effect=gateway_post).start()

    class ObserveASGI:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await self.app(scope, receive, send)
            headers = dict(scope["headers"])
            token = REQUEST_ID.set(headers.get(b"x-c03-id", b"sem-id").decode())
            emit("http_inicio", path=scope["path"])
            try:
                await self.app(scope, receive, send)
            finally:
                emit("http_fim")
                REQUEST_ID.reset(token)

    app.add_middleware(ObserveASGI)

    @asynccontextmanager
    async def lifespan(application):
        async def beat():
            while True:
                before = time.perf_counter()
                await asyncio.sleep(0.02)
                lag = time.perf_counter() - before - 0.02
                if lag > 0.05:
                    emit("loop_atrasado", lag_s=lag, inicio_espera=before)
        task = asyncio.create_task(beat())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    app.router.lifespan_context = lifespan

    @app.get("/__c03/health")
    async def health():
        return {"pid": os.getpid(), "t": time.perf_counter()}

    @app.post("/__c03/prepare")
    async def prepare(request: Request):
        body = await request.json()
        active.update(perfil=body["perfil"], usuarios=body["usuarios"])
        with SessionLocal() as db:
            for identity in active["usuarios"]:
                user = User(id_wpp=identity, name="Teste C03B", state=body["estado"])
                db.add(user)
                db.flush()
                db.add(Chat(user_id=user.id))
            db.commit()
        return {"preparado": True}

    @app.get("/__c03/snapshot")
    async def snapshot():
        with SessionLocal() as db:
            users = db.query(User).filter(User.id_wpp.in_(active["usuarios"])).all()
            ids = [u.id for u in users]
            chat_ids = [c.id for c in db.query(Chat).filter(Chat.user_id.in_(ids))]
            return {"usuarios": [{"id_wpp": u.id_wpp, "estado": u.state} for u in users],
                    "mensagens": [{"chat_id": m.chat_id, "sender": m.sender, "text": m.text}
                                  for m in db.query(Message).filter(Message.chat_id.in_(chat_ids)).order_by(Message.id)],
                    "auditoria": [{"usuario": e.user_id, "tipo": e.event_type, "meta": e.metadata_info}
                                  for e in db.query(AuditLog).filter(AuditLog.user_id.in_(ids)).order_by(AuditLog.id)]}

    @app.post("/__c03/stop")
    async def stop():
        server.should_exit = True
        return {"encerramento_solicitado": True}

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, loop="asyncio",
                                          access_log=False, log_level="warning"))
    (out / "servidor.json").write_text(json.dumps({"porta": port, "pid": os.getpid(), "workers": 1}), encoding="utf-8")
    try:
        server.run(sockets=[sock])
    finally:
        transport_client.close()
        engine.dispose()
        sock.close()
        events_file.close()
        autoenv.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
