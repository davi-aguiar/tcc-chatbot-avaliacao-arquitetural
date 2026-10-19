"""Executar da raiz; --gerar habilita uma consulta real se houver chave local."""
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
result = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "indice_reconstruido": False}

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    from app.main import setup_system, METRICAS_INDEXACAO
    retriever = setup_system()["servicos"]
    result.update(indice_reconstruido=True, metricas=dict(METRICAS_INDEXACAO))
    question = "Qual é a finalidade do Serviço Experimental C01?"
    docs = retriever.invoke(question)
    result["consulta"] = question
    result["documentos_recuperados"] = [
        {"posicao": i + 1, "fonte": d.metadata, "conteudo": d.page_content}
        for i, d in enumerate(docs)
    ]
    result["documento_c01_recuperado"] = any("C01-DOC-TESTE-2026" in d.page_content for d in docs)
    assert result["documento_c01_recuperado"], "Documento sintetico ausente dos resultados"
    result["chave_configurada"] = bool(os.getenv("GROQ_API_KEY"))
    result["geracao_executada"] = False
    if "--gerar" in sys.argv and result["chave_configurada"]:
        from api.services.nlp_service import NLPService
        from app.core.rag_pipeline import MODEL_NAME
        result["modelo"] = MODEL_NAME
        result["resposta"] = NLPService(retriever).process(question, user_name="Teste C01")
        result["geracao_executada"] = True
        assert result["resposta"], "Resposta vazia"
    result["situacao"] = "recuperacao_aprovada" if not result["geracao_executada"] else "geracao_executada_requer_analise_da_resposta"
except Exception as exc:
    # Não gravar mensagens de serviços remotos: podem conter detalhes de credenciais.
    result["situacao"] = "falha"
    result["tipo_erro"] = type(exc).__name__
    result["local_erro"] = [{"arquivo": Path(f.filename).name, "linha": f.lineno, "funcao": f.name} for f in traceback.extract_tb(exc.__traceback__)]
finally:
    result["fim"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (OUT / "rag-real.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "documentos_recuperados"}, ensure_ascii=True, indent=2), flush=True)
sys.exit(1 if result["situacao"] == "falha" else 0)
