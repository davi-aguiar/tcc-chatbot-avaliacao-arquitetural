import os

from langchain_community.embeddings import HuggingFaceEmbeddings

# all-MiniLM-L6-v2, o modelo anterior, e treinado majoritariamente em ingles e
# a base inteira esta em portugues. Este e o equivalente multilingue da mesma
# familia, sem exigir prefixo de query/passage como os modelos E5.
MODELO_PADRAO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=os.getenv("EMBEDDINGS_MODEL", MODELO_PADRAO)
    )
