"""Os 16 casos arquiteturais C04; executar pelo processo isolado de executar.py."""
import math
import os
from pathlib import Path
import re

if os.environ.get("C04_WORKER") != "1":
    raise RuntimeError("Execute docs/avaliacao/c04/executar.py para garantir o isolamento C04.")

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.adapters import embeddings, splitter, vector_store
from app.adapters.respostas import RESPOSTA_SEM_CONTEXTO
from app.core import ingestion, rag_pipeline
from app import main as assembly
from api.services.nlp_service import NLPService, SAUDACAO_INSTITUCIONAL


class LocalEmbeddings(Embeddings):
    """Vetores lexicais transparentes; sem modelo treinado ou qualidade semântica alegada."""
    def __init__(self):
        self.calls = []
        self.error = None

    def vector(self, text):
        words = re.findall(r"\w+", text.casefold())
        values = [float(words.count(term)) for term in ("aurora", "horizonte")]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def embed_documents(self, texts):
        self.calls.append({"tipo": "documentos", "quantidade": len(texts)})
        return [self.vector(text) for text in texts]

    def embed_query(self, text):
        self.calls.append({"tipo": "consulta", "texto": text})
        if self.error is not None:
            raise self.error
        return self.vector(text)


@pytest.fixture
def evidence(request):
    case_id = request.node.name.split("_")[1]
    row = request.config.c04_observations.setdefault(case_id, {"id": case_id})
    row["observacoes"] = {}
    return row["observacoes"]


@pytest.fixture
def corpus(request, monkeypatch):
    root = request.config.c04_out / "projeto-sintetico"
    monkeypatch.setattr(ingestion, "__file__", str(root / "app/core/ingestion.py"))
    return root / "data/servicos"


@pytest.fixture
def local_embeddings(monkeypatch):
    local = LocalEmbeddings()
    local.constructors = []

    def construct(**kwargs):
        local.constructors.append(kwargs)
        return local

    monkeypatch.setattr(embeddings, "HuggingFaceEmbeddings", construct)
    return local


@pytest.fixture
def resources(corpus, local_embeddings):
    docs = ingestion.load_servicos()
    chunks = splitter.split_docs(docs)
    model = embeddings.get_embeddings()
    index = vector_store.create_vector_store(chunks, model)
    retriever = vector_store.create_retriever(index, k=1)
    return docs, chunks, index, retriever, model


@pytest.fixture
def generator(monkeypatch):
    class LocalGenerator:
        def __init__(self):
            self.prompts = []
            self.response = "Resposta sintética C04."
            self.error = None

        def invoke(self, prompt):
            self.prompts.append(prompt.to_string())
            if self.error is not None:
                raise self.error
            return AIMessage(content=self.response)

    local = LocalGenerator()
    monkeypatch.setattr(rag_pipeline, "CACHED_LLM", RunnableLambda(local.invoke))
    return local


def test_I01_ingestao(corpus, evidence):
    docs = ingestion.load_servicos()
    evidence.update(documentos=[{"texto": d.page_content, "metadata": d.metadata} for d in docs])
    assert len(docs) == 2
    assert {Path(d.metadata["source"]).name for d in docs} == {"aurora.txt", "horizonte.txt"}
    for d in docs:
        assert d.page_content == Path(d.metadata["source"]).read_text(encoding="utf-8")
        assert "Serviço" in d.page_content and "é fictício" in d.page_content


def test_I02_diretorio_ausente(tmp_path, monkeypatch, evidence):
    monkeypatch.setattr(ingestion, "__file__", str(tmp_path / "ausente/app/core/ingestion.py"))
    with pytest.raises(FileNotFoundError) as observed:
        ingestion.load_servicos()
    evidence.update(erro_tipo=type(observed.value).__name__, mensagem=str(observed.value))


def test_D01_chunking(corpus, evidence):
    docs = ingestion.load_servicos()
    chunks = splitter.split_docs(docs)
    lengths = [len(c.page_content) for c in chunks]
    overlaps = []
    for left, right in zip(chunks, chunks[1:]):
        if left.metadata == right.metadata:
            overlaps.append(max([n for n in range(1, 201)
                                 if left.page_content[-n:] == right.page_content[:n]] or [0]))
    evidence.update(documentos=len(docs), chunks=len(chunks), tamanhos=lengths,
                    sobreposicoes=overlaps, metadados=[c.metadata for c in chunks])
    assert len(chunks) > len(docs)
    assert all(0 < size <= 1000 for size in lengths)
    assert any(overlaps)
    originals = {d.metadata["source"]: d.page_content for d in docs}
    assert all(c.page_content in originals[c.metadata["source"]] for c in chunks)


def check_retrieval(service, resources, evidence):
    docs, chunks, index, retriever, model = resources
    question = f"Qual é o horário do serviço {service}?"
    found = retriever.invoke(question)
    evidence.update(indice_tipo=type(index).__name__, vetores=index.index.ntotal,
                    chunks=len(chunks), resultados=[{"texto": d.page_content, "metadata": d.metadata} for d in found],
                    embeddings=model.calls)
    assert type(index).__name__ == "FAISS" and index.index.ntotal == len(chunks)
    assert len(found) == 1
    assert Path(found[0].metadata["source"]).stem == service.lower()
    assert f"C04-{service.upper()}-2026" in found[0].page_content
    assert any(c["tipo"] == "consulta" for c in model.calls)


def test_R01_recupera_aurora(resources, evidence):
    check_retrieval("Aurora", resources, evidence)


def test_R02_recupera_horizonte(resources, evidence):
    check_retrieval("Horizonte", resources, evidence)


def test_B01_montagem(corpus, local_embeddings, evidence):
    result = assembly.setup_system()
    metrics = dict(assembly.METRICAS_INDEXACAO)
    docs = result["servicos"].invoke("Informações do serviço Horizonte")
    evidence.update(chaves=list(result), metricas=metrics, construtores=local_embeddings.constructors,
                    embeddings=local_embeddings.calls, documentos_retornados=len(docs))
    assert list(result) == ["servicos"]
    assert metrics["n_documentos"] == 2 and metrics["n_chunks"] > 2
    assert all(name in metrics for name in ("carregamento_documentos_ms", "chunking_ms",
        "carregamento_embeddings_ms", "vetorizacao_e_indexacao_ms", "criacao_retriever_ms", "total_ms"))
    assert all(v >= 0 for k, v in metrics.items() if k.endswith("_ms"))
    assert docs and "HORIZONTE" in docs[0].page_content
    assert local_embeddings.constructors == [{"model_name": embeddings.MODELO_PADRAO}]


def test_B02_configuracao_embeddings(local_embeddings, monkeypatch, evidence):
    monkeypatch.setenv("EMBEDDINGS_MODEL", "c04-modelo-sintetico-sem-pesos")
    result = embeddings.get_embeddings()
    evidence.update(construtores=local_embeddings.constructors, objeto_local=result is local_embeddings)
    assert result is local_embeddings
    assert local_embeddings.constructors == [{"model_name": "c04-modelo-sintetico-sem-pesos"}]


def test_P01_prompt_parser_nlp(resources, generator, evidence):
    question = "Qual é o horário do serviço Aurora?"
    generator.response = "Resposta fixa para Aurora, somente para teste."
    answer = NLPService(resources[3]).process(question)
    evidence.update(pergunta=question, prompts=generator.prompts, resposta=answer, embeddings=resources[4].calls)
    assert answer == generator.response and isinstance(answer, str)
    assert len(generator.prompts) == 1
    prompt = generator.prompts[0]
    assert question in prompt and "C04-AURORA-2026" in prompt and "C04-HORIZONTE-2026" not in prompt
    assert "Use APENAS" in prompt and RESPOSTA_SEM_CONTEXTO in prompt


def test_P02_contexto_vazio(resources, generator, evidence):
    retriever = resources[3]
    retriever.search_kwargs["filter"] = {"source": "c04-origem-inexistente"}
    generator.response = RESPOSTA_SEM_CONTEXTO
    answer = NLPService(retriever).process("Qual é o horário do serviço Aurora?")
    evidence.update(prompts=generator.prompts, saida_gerador=generator.response, resposta_nlp=answer,
                    filtro=retriever.search_kwargs["filter"], embeddings=resources[4].calls)
    assert answer is None and len(generator.prompts) == 1
    assert "CONTEXTO:\n[]" in generator.prompts[0]
    assert "C04-AURORA-2026" not in generator.prompts[0]


def test_P03_resposta_vazia(resources, generator, evidence):
    generator.response = "  \n  "
    answer = NLPService(resources[3]).process("Detalhes do serviço Aurora")
    evidence.update(prompts=generator.prompts, saida_gerador=generator.response, resposta_nlp=answer)
    assert answer is None and len(generator.prompts) == 1
    assert "C04-AURORA-2026" in generator.prompts[0]


def test_E01_excecao_gerador(resources, generator, evidence):
    error = RuntimeError("C04: falha sintética do gerador")
    generator.error = error
    with pytest.raises(RuntimeError) as observed:
        NLPService(resources[3]).process("Detalhes do serviço Aurora")
    evidence.update(prompts=generator.prompts, erro_tipo=type(observed.value).__name__,
                    mesma_excecao=observed.value is error)
    assert observed.value is error and len(generator.prompts) == 1
    assert "C04-AURORA-2026" in generator.prompts[0]


def test_E02_excecao_recuperacao(resources, generator, evidence):
    error = RuntimeError("C04: falha sintética dos embeddings na busca")
    resources[4].error = error
    with pytest.raises(RuntimeError) as observed:
        NLPService(resources[3]).process("Detalhes do serviço Aurora")
    evidence.update(erro_tipo=type(observed.value).__name__, mesma_excecao=observed.value is error,
                    prompts=generator.prompts, embeddings=resources[4].calls)
    assert observed.value is error and not generator.prompts
    assert resources[4].calls[-1]["tipo"] == "consulta"


def test_L01_fabrica_sem_chave(monkeypatch, evidence):
    assert "GROQ_API_KEY" not in os.environ
    monkeypatch.setattr(rag_pipeline, "CACHED_LLM", None)
    with pytest.raises(ValueError, match="chave da API Groq") as observed:
        rag_pipeline.get_llm()
    evidence.update(erro_tipo=type(observed.value).__name__, mensagem=str(observed.value), cache_vazio=True)


def test_L02_entrada_vazia(resources, generator, evidence):
    before = len(resources[4].calls)
    nlp = NLPService(resources[3])
    answers = [nlp.process(""), nlp.process("   "), rag_pipeline.run_rag(resources[3], "  ")]
    evidence.update(respostas=answers, prompts=generator.prompts,
                    chamadas_embeddings_adicionais=len(resources[4].calls) - before)
    assert answers == [None, None, "Digite uma pergunta válida."]
    assert not generator.prompts and len(resources[4].calls) == before


def test_N01_saudacao_institucional(resources, generator, evidence):
    generator.response = "  " + SAUDACAO_INSTITUCIONAL + ". Como posso te ajudar?  "
    before = len(resources[4].calls)
    answer = NLPService(resources[3]).process("Olá!", user_name="Ana C04")
    evidence.update(prompts=generator.prompts, resposta=answer,
                    chamadas_embeddings_adicionais=len(resources[4].calls) - before)
    assert answer == "Oi, Ana C04! 😊\nComo posso te ajudar?"
    assert len(generator.prompts) == 1 and "Gere uma saudação" in generator.prompts[0]
    assert "C04-AURORA-2026" not in generator.prompts[0] and len(resources[4].calls) == before


def test_N02_saudacao_generica(resources, generator, evidence):
    generator.response = "Olá! Desculpe a demora. Resposta sintética sobre Aurora."
    answer = NLPService(resources[3]).process("Detalhes do serviço Aurora", user_name="Ana C04")
    evidence.update(prompts=generator.prompts, resposta=answer)
    assert answer == "Oi, Ana C04! 😊 Desculpe a demora. Resposta sintética sobre Aurora."
    assert len(generator.prompts) == 1 and "C04-AURORA-2026" in generator.prompts[0]
