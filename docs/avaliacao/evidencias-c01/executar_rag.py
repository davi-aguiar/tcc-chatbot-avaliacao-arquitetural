"""Executar da raiz; --gerar consulta real; --modelo ID adapta apenas o ensaio."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--gerar", action="store_true")
parser.add_argument("--modelo", help="Modelo remoto apenas neste processo experimental")
args = parser.parse_args()
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
    if args.gerar and result["chave_configurada"]:
        import asyncio
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from api.models.models import Base, User
        from api.services.chat_service import ChatService
        from api.services.nlp_service import NLPService
        from app.core import rag_pipeline
        result["modelo_original"] = rag_pipeline.MODEL_NAME
        if args.modelo:
            rag_pipeline.MODEL_NAME = args.modelo
            rag_pipeline.CACHED_LLM = None
        result["modelo"] = rag_pipeline.MODEL_NAME
        result["modelo_substituido_no_ensaio"] = bool(args.modelo)
        class NLPRegistrado(NLPService):
            def process(self, text, user_name=None):
                result["consulta_geracao"] = text
                try:
                    answer = super().process(text, user_name=user_name)
                except Exception as exc:
                    result["tipo_erro_geracao"] = type(exc).__name__
                    raise RuntimeError("Falha remota; tipo registrado no artefato") from None
                result["resposta_nlp"] = answer
                result["geracao_executada"] = True
                return answer

        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        result["percurso_real"] = []
        with sessionmaker(bind=engine)() as db:
            user = User(id_wpp="5500000000000", name="Teste C01", state="WAITING_MAIN_MENU")
            db.add(user)
            db.commit()
            service = ChatService(db, NLPRegistrado(retriever))
            for entrada, estado in [
                ("/menu", "WAITING_MAIN_MENU"),
                ("4", "WAITING_4_SERVICOS"),
                ("17", "WAITING_4_17_C01"),
                ("1", "WAITING_4_17_C01"),
                ("0", "WAITING_4_SERVICOS"),
                ("0", "WAITING_MAIN_MENU"),
            ]:
                response = asyncio.run(service.process_message(user.id_wpp, entrada))
                db.refresh(user)
                result["percurso_real"].append({"entrada": entrada, "estado": user.state, "saida": response.text})
                assert user.state == estado, "Estado inesperado no percurso real"
                if entrada == "1":
                    result["resposta"] = response.text
        assert result["consulta_geracao"] == question, "Consulta diferente da recuperacao"
        assert result["geracao_executada"], "Geracao nao concluida"
        assert result.get("resposta_nlp"), "Resposta NLP vazia ou sem contexto"
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
