"""Montagem do indice vetorial, com medicao de cada etapa.

setup_system roda uma unica vez, na subida do processo. As duracoes ficam em
METRICAS_INDEXACAO e vao para o log: e o unico ponto em que o custo de boot e
observavel. A doc do projeto afirma que esse tempo e gasto carregando o modelo
de embeddings, e nao vetorizando os documentos, mas isso nunca foi medido —
cronometrar etapa a etapa e o que permite confirmar ou refutar a afirmacao.
"""
import logging
import time

from app.adapters.splitter import split_docs
from app.core.ingestion import load_servicos
from app.adapters.embeddings import get_embeddings
from app.adapters.vector_store import create_vector_store, create_retriever

logger = logging.getLogger("AppLogger")

# Preenchido por setup_system. Dicionario de modulo (mutado no lugar, nunca
# reatribuido) para que `from app.main import METRICAS_INDEXACAO` continue
# enxergando o conteudo depois da montagem.
METRICAS_INDEXACAO: dict = {}


def setup_system():
    metricas = {}

    def cronometrar(nome, funcao):
        """Roda a etapa e guarda quanto ela levou, em milissegundos.

        perf_counter e nao time(): e monotonico, entao ajuste de relogio no meio
        do boot nao produz duracao negativa.
        """
        inicio = time.perf_counter()
        resultado = funcao()
        metricas[f"{nome}_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
        return resultado

    inicio_total = time.perf_counter()

    docs_servicos = cronometrar("carregamento_documentos", load_servicos)
    chunks_servicos = cronometrar("chunking", lambda: split_docs(docs_servicos))
    embeddings = cronometrar("carregamento_embeddings", get_embeddings)
    vector_store = cronometrar(
        "vetorizacao_e_indexacao",
        lambda: create_vector_store(chunks_servicos, embeddings),
    )
    retriever = cronometrar("criacao_retriever", lambda: create_retriever(vector_store))

    metricas["total_ms"] = round((time.perf_counter() - inicio_total) * 1000, 2)
    metricas["n_documentos"] = len(docs_servicos)
    metricas["n_chunks"] = len(chunks_servicos)

    METRICAS_INDEXACAO.clear()
    METRICAS_INDEXACAO.update(metricas)
    logger.info("INDEXACAO_CONCLUIDA %s", metricas)

    return {"servicos": retriever}
