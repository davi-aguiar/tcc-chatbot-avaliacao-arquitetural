"""Verificações locais do instrumento; não são respostas avaliadas no C05."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import socket
from types import SimpleNamespace
from unittest.mock import patch

import pytest

SPEC = importlib.util.spec_from_file_location("executor_c05", Path(__file__).with_name("executar.py"))
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


def test_matriz_e_trechos_correspondem_ao_corpus():
    spec = executor.load(executor.HERE / "casos.json")
    executor.validate_cases(spec, executor.ROOT / "data/servicos")
    assert [(r, c["id"]) for r, c in executor.schedule(spec)] == [
        (r, f"P{i:02d}") for r in (1, 2) for i in range(1, 7)]


def test_trecho_inexistente_impede_coleta():
    spec = deepcopy(executor.load(executor.HERE / "casos.json"))
    spec["casos"][0]["fatos_esperados"][0]["trecho"] = "TRECHO-C05-INEXISTENTE"
    with pytest.raises(ValueError, match="Trecho esperado ausente"):
        executor.validate_cases(spec, executor.ROOT / "data/servicos")


@pytest.mark.parametrize("operation", ["dns", "connect", "udp"])
def test_preparacao_bloqueia_rede(operation):
    with executor.no_network(), pytest.raises(RuntimeError, match="rede bloqueada"):
        if operation == "dns":
            socket.getaddrinfo("c05.invalid", 443)
        elif operation == "connect":
            with socket.socket() as sock:
                sock.connect(("127.0.0.1", 9))
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(b"c05", ("127.0.0.1", 9))


@pytest.mark.parametrize("output", ["Resposta documental sintética.",
    "Desculpe, não encontrei essa informação específica nos meus documentos.",
    "Não encontrei essa informação, mas o prazo é 123 dias."])
def test_observacao_preserva_prompt_e_nao_duplica_chamadas(output):
    # Todo o stack é importado sem carregar automaticamente credenciais locais.
    with patch("dotenv.load_dotenv", return_value=False), executor.no_network():
        from langchain_core.documents import Document
        from langchain_core.messages import AIMessage
        from langchain_core.runnables import RunnableLambda
        from app.adapters.prompts import rag_prompt
        from app.adapters.respostas import sem_contexto
        from app.core import rag_pipeline

        case = executor.load(executor.HERE / "casos.json")["casos"][0]
        docs = [Document(page_content="C05: contexto exato.", metadata={"source": "c05-teste.txt"})]
        received = []
        queries = []
        sentinel = object()

        def retrieve(question):
            queries.append(question)
            return docs

        def generate(prompt):
            received.append(prompt.to_string())
            return AIMessage(content=output, response_metadata={"finish_reason": "stop"})

        with patch.object(rag_pipeline, "CACHED_LLM", sentinel):
            row = executor.invoke_observed(RunnableLambda(retrieve), RunnableLambda(generate), case, 1)
            assert rag_pipeline.CACHED_LLM is sentinel
        assert queries == [case["pergunta"]] and len(received) == 1
        assert row["prompt"] == received[0] == rag_prompt.invoke({
            "context": docs, "question": case["pergunta"]}).to_string()
        assert row["contexto"] == executor.serialize_docs(docs)
        assert row["chamadas_recuperador"] == row["chamadas_gerador"] == 1
        assert row["resposta_original"] == output and row["erro_tipo"] is None
        assert row["saida_nlp"] == (None if sem_contexto(output) else output)
        # Até a resposta com número inventado e núcleo de ausência fica pendente.
        assert executor.review_sheet(row, case)["estado"] == "pendente"


@pytest.mark.parametrize("stage", ["recuperacao", "geracao"])
def test_erro_preserva_evidencia_sem_persistir_mensagem(stage):
    with patch("dotenv.load_dotenv", return_value=False), executor.no_network():
        from langchain_core.documents import Document
        from langchain_core.runnables import RunnableLambda

        case = executor.load(executor.HERE / "casos.json")["casos"][0]

        def fail(value):
            raise RuntimeError("MENSAGEM-NAO-DEVE-SER-PERSISTIDA")

        retrieve = RunnableLambda(fail if stage == "recuperacao" else lambda _: [Document(page_content="C05")])
        row = executor.invoke_observed(retrieve, RunnableLambda(fail), case, 1)
        assert row["erro_tipo"] == "RuntimeError"
        assert "MENSAGEM-NAO-DEVE-SER-PERSISTIDA" not in str(row)
        assert row["chamadas_gerador"] == (0 if stage == "recuperacao" else 1)
        assert bool(row["prompt"]) == (stage == "geracao")
        assert executor.review_sheet(row, case)["estado"] == "nao_avaliado_erro"


def test_presenca_da_fonte_nao_significa_presenca_do_fato():
    case = executor.load(executor.HERE / "casos.json")["casos"][0]
    docs = [{"indice": 1, "conteudo": "Somente contato, sem passos de acesso.",
             "metadados": {"source": case["fontes_esperadas"][0]}}]
    result = executor.retrieval_diagnostics(case, docs)
    assert all(result["fontes_esperadas_presentes"].values())
    assert all(fact["chunks"] == [] for fact in result["trechos_literais"])


def test_integridade_detecta_alteracao_de_fonte(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, "ROOT", tmp_path)
    source = tmp_path / "fonte.txt"
    source.write_text("antes", encoding="utf-8")
    hashes = {"fonte.txt": executor.digest(source)}
    source.write_text("depois", encoding="utf-8")
    assert executor.finish_manifest(tmp_path, hashes) is False
    assert executor.load(tmp_path / "integridade-fontes.json")["alteradas"] == ["fonte.txt"]


@pytest.mark.parametrize("model_available", [True, False])
def test_coleta_com_sdk_real_e_transporte_sintetico(tmp_path, monkeypatch, model_available):
    """Exercita os 12 registros e o SDK sem enviar requisições externas."""
    import httpx
    from langchain_core.documents import Document
    from langchain_core.runnables import RunnableLambda

    snapshot = tmp_path / "pesos-sinteticos"
    snapshot.mkdir()
    (snapshot / "model.safetensors").write_bytes(b"c05-teste-instrumento")
    requests = []

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "c05-modelo-sintetico"}] if model_available else []})
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "c05-sintetico", "object": "chat.completion", "created": 0,
            "model": "c05-modelo-sintetico", "choices": [{"index": 0, "finish_reason": "stop",
                "message": {"role": "assistant", "content": "C05: resposta sintética do instrumento."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}})

    original_client = httpx.Client

    class LocalClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handle)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", LocalClient)
    monkeypatch.setenv("GROQ_API_KEY", "c05-chave-sintetica-nao-real")
    monkeypatch.setattr(executor, "local_setup", lambda _: RunnableLambda(
        lambda question: [Document(page_content="C05: contexto sintético do instrumento.")]))
    args = SimpleNamespace(modo="coletar", embeddings_snapshot=snapshot,
                           saida=tmp_path / "saida", modelo="c05-modelo-sintetico")
    with executor.no_network():
        result = executor.collect(args)
    out, = args.saida.iterdir()
    execution = executor.load(out / "execucao.json")
    assert result == (0 if model_available else 1)
    if not model_available:
        assert requests == [] and execution["coleta_completa"] is False
        assert execution["julgamento"] == "nao_avaliado"
        return
    assert len(requests) == execution["respostas_obtidas"] == 12
    assert execution["coleta_completa"] and execution["instrumentacao_valida"]
    assert execution["julgamento"] == "pendente_revisao"
    assert all(r["estado"] == "pendente" for r in executor.load(out / "revisao.json"))
    for round_number, case in executor.schedule(executor.load(executor.HERE / "casos.json")):
        row = executor.load(out / f"{case['id']}-R{round_number}.json")
        assert row["tentativas_http"][0]["status"] == 200
        assert row["prompt"] == requests.pop(0)["messages"][0]["content"]
        assert row["resposta_original"] == row["saida_nlp"] == "C05: resposta sintética do instrumento."
    assert "c05-chave-sintetica-nao-real" not in "".join(
        p.read_text(encoding="utf-8") for p in out.glob("*.json"))
