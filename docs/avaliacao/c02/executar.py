"""Instrumento C02; executar da raiz. Não altera Python funcional nem usa o banco configurado."""
import argparse
import asyncio
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest(args):
    files = [p for folder in ("api", "app", "data/servicos")
             for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".json", ".txt")]
    files += [HERE / "casos.json", Path(__file__), HERE.parent / "C02-protocolo.md"]
    return {
        "inicio_utc": now(), "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"), "git_status": git("status", "--short"),
        "python": sys.version, "executavel": sys.executable, "plataforma": platform.platform(),
        "processador": platform.processor(), "cpus_logicas": os.cpu_count(),
        "memoria_fisica_bytes": physical_memory(),
        "dependencias": sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()}),
        "chave_groq_presente": bool(os.getenv("GROQ_API_KEY")),
        "embeddings_model": os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        "cache": {k: os.getenv(k) for k in ("HF_HOME", "HF_HUB_CACHE", "SENTENCE_TRANSFORMERS_HOME", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")},
        "argumentos": vars(args), "banco": "SQLite em memoria; descartavel; sem gateway/HTTP",
        "sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
    }


def physical_memory():
    if os.name != "nt":
        return None
    import ctypes
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "avail", "page", "avail_page", "virtual", "avail_virtual", "extended")]
    info = Memory()
    info.length = ctypes.sizeof(info)
    return info.total if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)) else None


def offline_cache():
    # Cache obrigatório para a série aquecida; falta de pesos vira falha, não download oculto.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def startup_worker(output):
    result = {"inicio_utc": now(), "pid": os.getpid(), "cache_offline": True}
    start = time.perf_counter()
    try:
        from app.main import setup_system, METRICAS_INDEXACAO
        retriever = setup_system()["servicos"]
        result["metricas"] = dict(METRICAS_INDEXACAO)
        # Verificação fora do intervalo setup_system; boot não é só construir um objeto.
        docs = retriever.invoke("O que é o serviço CEO?")
        result["documentos_verificacao"] = len(docs)
        result["sucesso"] = bool(docs)
    except Exception as exc:
        result.update(sucesso=False, erro_tipo=type(exc).__name__)
    result.update(fim_utc=now(), processo_ate_verificacao_ms=(time.perf_counter() - start) * 1000)
    save(output, result)
    return 0 if result["sucesso"] else 1


def startups(out):
    results = []
    # A primeira execução prepara/verifica o cache separadamente da série de três.
    for index in range(4):
        label = "preparacao" if index == 0 else f"inicializacao-{index}"
        dest = out / f"{label}.json"
        start = time.perf_counter()
        with (out / f"{label}.log").open("w", encoding="utf-8") as log:
            try:
                proc = subprocess.run([sys.executable, str(Path(__file__)), "worker", "--output", str(dest)],
                                      cwd=ROOT, stdout=log, stderr=log, timeout=900)
                result = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {"sucesso": False}
                result["exit_code"] = proc.returncode
            except subprocess.TimeoutExpired:
                result = {"sucesso": False, "erro_tipo": "TimeoutExpired"}
        result.update(etapa=label, processo_pai_ms=(time.perf_counter() - start) * 1000)
        save(dest, result)
        results.append(result)
        print(json.dumps({"etapa": label, "sucesso": result["sucesso"], "metricas": result.get("metricas")}), flush=True)
        if index == 0 and not result["sucesso"]:
            break
    measured = results[1:]
    save(out / "resumo.json", {
        "preparacao_separada": results[0], "n": len(measured),
        "sucessos": sum(r["sucesso"] for r in measured),
        "total_setup_ms_sucessos": describe([r["metricas"]["total_ms"] for r in measured if r["sucesso"]]),
    })
    return len(measured) == 3 and all(r["sucesso"] for r in results)


def describe(values):
    return {"n": len(values), "mediana": statistics.median(values), "minimo": min(values), "maximo": max(values)} if values else {"n": 0}


def messages(args, out):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api.models.models import Base, User, Chat, AuditLog
    from api.services.chat_service import ChatService
    from api.services.menu_handlers import TEXTS

    cases = json.loads((HERE / "casos.json").read_text(encoding="utf-8"))
    if args.escopo != "todos":
        cases = [c for c in cases if (c["percurso"] == "estatico") == (args.escopo == "estatico")]
    save(out / "casos.json", cases)
    need_rag = any(c["percurso"] != "estatico" for c in cases)
    if need_rag and not os.getenv("GROQ_API_KEY"):
        save(out / "impedimento.json", {"motivo": "GROQ_API_KEY ausente", "mensagens_medidas": 0})
        return False

    real_nlp = None
    if need_rag:
        from app.main import setup_system, METRICAS_INDEXACAO
        from api.services.nlp_service import NLPService
        from app.core import rag_pipeline
        original = rag_pipeline.MODEL_NAME
        if args.modelo:
            rag_pipeline.MODEL_NAME = args.modelo
            rag_pipeline.CACHED_LLM = None
        real_nlp = NLPService(setup_system()["servicos"])
        llm = rag_pipeline.get_llm()
        save(out / "modelo.json", {
            "original": original, "utilizado": rag_pipeline.MODEL_NAME,
            "configuracao_adaptada": rag_pipeline.MODEL_NAME != original,
            "temperatura": llm.temperature, "max_tokens": llm.max_tokens,
            "max_retries": llm.max_retries, "timeout": str(llm.request_timeout),
            "setup_fora_da_coleta": dict(METRICAS_INDEXACAO),
        })

    class Observado:
        """Encaminha ao NLP real e relança a mesma exceção; captura falhas ocultadas no texto livre."""
        def __init__(self):
            self.calls = []

        def process(self, text, user_name=None):
            record = {"consulta": text}
            self.calls.append(record)
            try:
                if real_nlp is None:
                    raise AssertionError("RAG inesperado na navegacao estatica")
                answer = real_nlp.process(text, user_name=user_name)
                record["sem_resposta"] = not bool(answer)
                return answer
            except Exception as exc:
                record["erro_tipo"] = type(exc).__name__
                raise

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    rows = []
    with sessionmaker(bind=engine)() as db:
        for index, case in enumerate(cases):
            user = User(id_wpp=f"550000000{index:04d}", name="Teste C02", state=case["estado"])
            db.add(user)
            db.flush()
            db.add(Chat(user_id=user.id))
        db.commit()

        async def run():
            # Um loop e um processo por lote; todos os casos aquecidos antes da coleta.
            for phase, count in (("aquecimento", 1), ("medicao", 5)):
                for rep in range(1, count + 1):
                    for index, case in enumerate(cases):
                        user = db.query(User).filter_by(id_wpp=f"550000000{index:04d}").one()
                        user.state = case["estado"]
                        db.commit()
                        # Materializa atributos antes do intervalo externo, igual para todas as entradas.
                        identity, user_id = user.id_wpp, user.id
                        last_id = db.query(AuditLog.id).order_by(AuditLog.id.desc()).first()
                        last_id = last_id[0] if last_id else 0
                        observed = Observado()
                        service = ChatService(db, observed)
                        row = dict(case, fase=phase, repeticao=rep, inicio_utc=now())
                        start = time.perf_counter()
                        try:
                            response = await service.process_message(identity, case["entrada"])
                            row["resposta"] = response.text
                        except Exception as exc:
                            row["erro_tipo"] = type(exc).__name__
                        row["externo_ms"] = (time.perf_counter() - start) * 1000
                        db.refresh(user)
                        row["estado_observado"] = user.state
                        events = db.query(AuditLog).filter(AuditLog.id > last_id, AuditLog.user_id == user_id).order_by(AuditLog.id).all()
                        row["eventos"] = [{"tipo": e.event_type, "meta": e.metadata_info} for e in events]
                        row["nlp"] = observed.calls
                        sent = [e for e in events if e.event_type == "MESSAGE_SENT"]
                        row["total_ms"] = sent[-1].metadata_info.get("duracao_total_ms") if sent else None
                        row["rag_ms"] = sent[-1].metadata_info.get("duracao_rag_ms") if sent else None
                        state_ok = user.state == case["estado_saida"]
                        audit_ok = len(sent) == 1 and not any(e.event_type == "MESSAGE_FAILED" for e in events)
                        if case["percurso"] == "estatico":
                            behavior_ok = not observed.calls and row.get("resposta") == TEXTS[case["estado_saida"]]["text"]
                        else:
                            behavior_ok = (len(observed.calls) == 1 and observed.calls[0].get("consulta") == case["consulta"]
                                           and not observed.calls[0].get("erro_tipo") and observed.calls[0].get("sem_resposta") is False)
                        row["sucesso"] = state_ok and audit_ok and behavior_ok and "erro_tipo" not in row
                        rows.append(row)
                        # Persiste incrementalmente: uma interrupção não apaga as tentativas anteriores.
                        save(out / "mensagens.json", rows)
                        print(json.dumps({"fase": phase, "caso": case["id"], "repeticao": rep, "sucesso": row["sucesso"], "total_ms": row["total_ms"]}), flush=True)
        asyncio.run(run())
    engine.dispose()
    measured = [r for r in rows if r["fase"] == "medicao"]
    with (out / "medicoes.csv").open("w", newline="", encoding="utf-8") as handle:
        columns = ["id", "percurso", "repeticao", "entrada", "estado", "estado_observado", "sucesso", "total_ms", "rag_ms", "externo_ms"]
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(measured)
    groups = {}
    for key in sorted({r["id"] for r in measured} | {r["percurso"] for r in measured}):
        group = [r for r in measured if key in (r["id"], r["percurso"])]
        groups[key] = {"tentativas": len(group), "sucessos": sum(r["sucesso"] for r in group), "falhas": sum(not r["sucesso"] for r in group),
                       "total_ms_sucessos": describe([r["total_ms"] for r in group if r["sucesso"]]),
                       "rag_ms_sucessos": describe([r["rag_ms"] for r in group if r["sucesso"] and r["rag_ms"] is not None]),
                       "externo_ms_falhas": describe([r["externo_ms"] for r in group if not r["sucesso"]])}
    save(out / "resumo.json", groups)
    return all(r["sucesso"] for r in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=["inicializacao", "mensagens", "worker"])
    parser.add_argument("--escopo", choices=["estatico", "rag", "todos"], default="todos")
    parser.add_argument("--modelo", help="Adapta somente o instrumento; preserva tentativas em diretórios distintos")
    parser.add_argument("--output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    os.chdir(ROOT)
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    offline_cache()
    if args.modo == "worker":
        return startup_worker(args.output)
    out = HERE.parent / "evidencias-c02" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + args.modo + "-" + args.escopo + "-" + uuid.uuid4().hex[:6])
    out.mkdir(parents=True, exist_ok=False)
    save(out / "ambiente.json", manifest(args))
    # Logs de aplicação em arquivo: evita expor detalhes de exceções do cliente remoto.
    # Auditoria estruturada real é guardada em mensagens.json; exceções NLP, por tipo.
    logging.disable(logging.CRITICAL)
    print(str(out.relative_to(ROOT)), flush=True)
    try:
        success = startups(out) if args.modo == "inicializacao" else messages(args, out)
        save(out / "execucao.json", {"fim_utc": now(), "concluiu_sem_falhas": success})
        return 0 if success else 1
    except Exception as exc:
        save(out / "execucao.json", {"fim_utc": now(), "concluiu_sem_falhas": False, "erro_tipo": type(exc).__name__})
        print(type(exc).__name__, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
