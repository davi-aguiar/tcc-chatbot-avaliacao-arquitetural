"""C05: preparação local e coleta real, sem modificar a aplicação."""
import argparse
from contextlib import contextmanager
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
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
SNAPSHOT = (Path.home() / ".cache/huggingface/hub/"
            "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots" / REVISION)
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


@contextmanager
def no_network():
    def deny(*args, **kwargs):
        raise RuntimeError("C05: rede bloqueada na preparação local")
    with patch.object(socket.socket, "connect", deny), patch.object(socket.socket, "connect_ex", deny), \
            patch.object(socket.socket, "sendto", deny), patch.object(socket, "getaddrinfo", deny):
        yield


def validate_cases(spec, corpus):
    cases = spec["casos"]
    if spec["repeticoes"] != 2 or [c["id"] for c in cases] != [f"P{i:02d}" for i in range(1, 7)]:
        raise ValueError("Matriz C05 inválida")
    if [c["tipo"] for c in cases] != ["respondivel"] * 3 + ["ausente"] * 2 + ["distincao"]:
        raise ValueError("Tipos de caso C05 inválidos")
    for case in cases:
        for source in case["fontes_esperadas"]:
            if not (corpus / source).is_file():
                raise ValueError("Fonte esperada inexistente")
        for fact in case["fatos_esperados"]:
            if fact["trecho"] not in (corpus / fact["fonte"]).read_text(encoding="utf-8"):
                raise ValueError(f"Trecho esperado ausente: {case['id']}/{fact['id']}")


def schedule(spec):
    return [(round_number, case) for round_number in range(1, spec["repeticoes"] + 1)
            for case in spec["casos"]]


def serialize_docs(docs):
    return [{"indice": index, "conteudo": doc.page_content, "metadados": doc.metadata}
            for index, doc in enumerate(docs, 1)]


def retrieval_diagnostics(case, docs):
    sources = {Path(d["metadados"].get("source", "")).name for d in docs}
    return {
        "fontes_esperadas_presentes": {name: name in sources for name in case["fontes_esperadas"]},
        "trechos_literais": [{"fato": fact["id"], "chunks": [d["indice"] for d in docs
            if Path(d["metadados"].get("source", "")).name == fact["fonte"]
            and fact["trecho"] in d["conteudo"]]} for fact in case["fatos_esperados"]],
        "aviso": "Diagnóstico literal, sem julgamento semântico; outras fontes exigem revisão."
    }


def invoke_observed(retriever, llm, case, round_number):
    """Uma passagem real no NLP; os observadores devolvem os objetos originais."""
    from langchain_core.runnables import RunnableLambda
    from app.adapters.respostas import RESPOSTA_SEM_CONTEXTO, sem_contexto
    from app.core import rag_pipeline
    from api.services.nlp_service import NLPService

    row = {"id": f"{case['id']}-R{round_number}", "caso": case["id"], "rodada": round_number,
           "pergunta": case["pergunta"], "inicio_utc": now(), "contexto": [], "prompt": None,
           "resposta_original": None, "saida_nlp": None, "erro_tipo": None,
           "chamadas_recuperador": 0, "chamadas_gerador": 0}

    def retrieve(question):
        row["chamadas_recuperador"] += 1
        docs = retriever.invoke(question)
        row["contexto"] = serialize_docs(docs)
        return docs

    def generate(prompt):
        row["chamadas_gerador"] += 1
        row["prompt"] = prompt.to_string()
        message = llm.invoke(prompt)
        row["resposta_original"] = message.content
        row["metadados_geracao"] = {key: message.response_metadata.get(key)
            for key in ("model_name", "finish_reason", "token_usage", "system_fingerprint")}
        row["uso_tokens"] = message.usage_metadata
        return message

    with patch.object(rag_pipeline, "CACHED_LLM", RunnableLambda(generate)):
        try:
            row["saida_nlp"] = NLPService(RunnableLambda(retrieve)).process(case["pergunta"])
        except Exception as exc:
            row["erro_tipo"] = type(exc).__name__
    raw = row["resposta_original"]
    row["frase_ausencia_exata"] = isinstance(raw, str) and raw.strip() == RESPOSTA_SEM_CONTEXTO
    row["ausencia_reconhecida"] = sem_contexto(raw) if isinstance(raw, str) else None
    row["diagnostico_recuperacao"] = retrieval_diagnostics(case, row["contexto"])
    row["fim_utc"] = now()
    return row


def review_sheet(row, case):
    return {"id": row["id"], "estado": "pendente" if row["erro_tipo"] is None else "nao_avaliado_erro",
            "revisor": None, "afirmacoes": [],
            "instrucao_afirmacoes": "Para cada afirmação: texto, sustentada/não sustentada/contraditória/ambígua, chunk e trecho literal.",
            "fatos_esperados": [{"id": fact["id"], "presenca_resposta": None, "apoio_contexto": None}
                                for fact in case["fatos_esperados"]],
            "recuperacao": None, "fidelidade": None, "completude": None,
            "abstencao_adequada": None, "confusao_servicos": None,
            "ambiguidade_documental": None, "observacoes": None}


def preserved_files():
    files = [p for folder in ("app", "api", "data/servicos") for p in (ROOT / folder).rglob("*")
             if p.is_file() and p.suffix in (".py", ".json", ".txt") and "__pycache__" not in p.parts]
    return sorted(set(files + list(HERE.glob("*.py")) + [HERE / "casos.json", HERE.parent / "C05-protocolo.md"]))


def preserve(out, snapshot, mode):
    sources = preserved_files()
    hashes = {}
    for source in sources:
        relative = source.relative_to(ROOT)
        target = out / "fontes" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[relative.as_posix()] = digest(source)
    environment = {
        "inicio_utc": now(), "modo": mode, "python": sys.version, "plataforma": platform.platform(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip(),
        "dependencias": sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()}),
        "sha256": hashes, "embeddings_snapshot": str(snapshot),
        "embeddings_sha256": {p.relative_to(snapshot).as_posix(): digest(p)
                              for p in sorted(snapshot.rglob("*")) if p.is_file()}}
    save(out / "ambiente.json", environment)
    return hashes


def finish_manifest(out, hashes):
    changed = [name for name, original in hashes.items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != original]
    save(out / "integridade-fontes.json", {"fontes_inalteradas": not changed, "alteradas": changed})
    return not changed


def local_setup(snapshot):
    if not (snapshot / "model.safetensors").is_file():
        raise FileNotFoundError("Pesos locais não encontrados; nenhuma transferência será feita")
    from app.main import setup_system
    return setup_system()["servicos"]


def collect(args):
    from dotenv import dotenv_values
    spec = load(HERE / "casos.json")
    validate_cases(spec, ROOT / "data/servicos")
    key = os.environ.get("GROQ_API_KEY") or dotenv_values(ROOT / ".env").get("GROQ_API_KEY")
    if args.modo == "coletar" and not key:
        raise ValueError("Credencial Groq ausente; configure GROQ_API_KEY localmente, sem enviar a chave ao chat")
    snapshot = args.embeddings_snapshot.resolve()
    if not snapshot.is_dir():
        raise FileNotFoundError("Snapshot de embeddings ausente")
    out = args.saida / f"{datetime.now():%Y%m%d-%H%M%S}-{args.modo}-{uuid.uuid4().hex[:6]}"
    out.mkdir(parents=True, exist_ok=False)
    print(json.dumps({"lote": str(out), "modo": args.modo}, ensure_ascii=False), flush=True)
    hashes = preserve(out, snapshot, args.modo)
    execution = {"inicio_utc": now(), "modo": args.modo, "credencial_presente": bool(key),
                 "respostas_previstas": 12, "respostas_obtidas": 0, "julgamento": "nao_avaliado",
                 "coleta_completa": False, "erro_tipo": None}
    rows = []
    runtime = out / "cache-runtime"
    settings = {"EMBEDDINGS_MODEL": str(snapshot), "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1", "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING": "false",
                "LANGCHAIN_TRACING_V2": "false", "PYTHON_DOTENV_DISABLED": "1",
                "HF_HOME": str(runtime), "SENTENCE_TRANSFORMERS_HOME": str(runtime),
                "HF_HUB_CACHE": str(runtime / "hub"), "TRANSFORMERS_CACHE": str(runtime / "transformers")}
    with patch.dict(os.environ, settings), patch("dotenv.load_dotenv", return_value=False):
        try:
            with no_network():
                retriever = local_setup(snapshot)
                if args.modo == "preparar":
                    for case in spec["casos"]:
                        docs = serialize_docs(retriever.invoke(case["pergunta"]))
                        rows.append({"id": case["id"], "pergunta": case["pergunta"], "contexto": docs,
                                     "diagnostico_recuperacao": retrieval_diagnostics(case, docs)})
                        save(out / "recuperacao.json", rows)
                    execution["preparacao_completa"] = len(rows) == 6
                    execution["coleta_completa"] = False
            if args.modo == "coletar":
                import httpx
                from langchain_groq import ChatGroq
                from app.core.rag_pipeline import MODEL_NAME

                model = args.modelo or MODEL_NAME
                configuration = {"modelo": model, "modelo_padrao_codigo": MODEL_NAME,
                                 "modelo_alternativo": model != MODEL_NAME,
                                 "temperature": 0.1, "max_tokens": 500, "timeout_s": 60, "max_retries": 2,
                                 "timeout_explicito_adaptado": True, "retriever_k": 10}
                save(out / "configuracao.json", configuration)
                active = {"attempts": []}

                def on_request(request):
                    active["attempts"].append({"tentativa": len(active["attempts"]) + 1,
                                                "inicio_utc": now(), "status": None})

                def on_response(response):
                    active["attempts"][-1].update(status=response.status_code, fim_utc=now())

                with httpx.Client(timeout=60, trust_env=False, follow_redirects=False) as model_client:
                    response = model_client.get("https://api.groq.com/openai/v1/models",
                                                headers={"Authorization": f"Bearer {key}"})
                    listing = {"data_utc": now(), "status": response.status_code, "modelos": []}
                    if response.status_code == 200:
                        listing["modelos"] = sorted(item["id"] for item in response.json().get("data", []))
                    save(out / "modelos-disponiveis.json", listing)
                    if response.status_code != 200 or model not in listing["modelos"]:
                        raise RuntimeError("Modelo escolhido indisponível; sem substituição automática")
                with httpx.Client(timeout=60, trust_env=False, follow_redirects=False,
                                  event_hooks={"request": [on_request], "response": [on_response]}) as client:
                    llm = ChatGroq(model=model, temperature=0.1, max_tokens=500, timeout=60,
                                   max_retries=2, api_key=key, http_client=client)
                    reviews = []
                    for round_number, case in schedule(spec):
                        active["attempts"] = []
                        row = invoke_observed(retriever, llm, case, round_number)
                        row["tentativas_http"] = active["attempts"]
                        rows.append(row)
                        save(out / f"{row['id']}.json", row)
                        reviews.append(review_sheet(row, case))
                        save(out / "revisao.json", reviews)
                        print(json.dumps({"id": row["id"], "erro_tipo": row["erro_tipo"]}), flush=True)
                execution["respostas_obtidas"] = sum(r["erro_tipo"] is None and
                                                      isinstance(r["resposta_original"], str) for r in rows)
                execution["coleta_completa"] = len(rows) == 12 and execution["respostas_obtidas"] == 12
                execution["instrumentacao_valida"] = len(rows) == 12 and all(
                    r["chamadas_recuperador"] == 1 and r["chamadas_gerador"] == 1 and r["prompt"]
                    for r in rows)
                execution["julgamento"] = "pendente_revisao" if execution["coleta_completa"] else "nao_avaliado_integralmente"
        except Exception as exc:
            execution["erro_tipo"] = type(exc).__name__
        finally:
            execution["fontes_inalteradas"] = finish_manifest(out, hashes)
            execution["fim_utc"] = now()
            save(out / "execucao.json", execution)
    print(json.dumps(execution, ensure_ascii=False), flush=True)
    complete = execution.get("preparacao_completa", False) if args.modo == "preparar" else (
        execution["coleta_completa"] and execution.get("instrumentacao_valida", False))
    return 0 if complete and execution["fontes_inalteradas"] and not execution["erro_tipo"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=("preparar", "coletar"))
    parser.add_argument("--modelo", help="Modelo explícito; padrão do código se omitido")
    parser.add_argument("--embeddings-snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--saida", type=Path, default=HERE.parent / "evidencias-c05")
    args = parser.parse_args()
    try:
        return collect(args)
    except Exception as exc:
        # Mensagens internas não contêm valores de credenciais; erros externos só por tipo.
        print(json.dumps({"erro_tipo": type(exc).__name__, "coleta_iniciada": False}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
