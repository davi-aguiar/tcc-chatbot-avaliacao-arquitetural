"""Deteccao de saudacao sem chamar o LLM.

Antes toda mensagem de texto livre gastava uma requisicao a Groq so para
decidir entre "greeting" e "question" — dobrando latencia e custo para
reconhecer "oi".

Modulo sem imports de proposito: da para testar sem carregar LangChain.
"""
import unicodedata

SAUDACOES = frozenset(
    {
        "oi", "ola", "opa", "salve", "alo",
        "eai", "e ai", "eae", "e ae", "iai", "i ai",
        "bom dia", "boa tarde", "boa noite",
        "oi tudo bem", "ola tudo bem", "tudo bem", "tudo bom",
        "hey", "hi", "hello",
    }
)

# Mensagem longa nao e saudacao, mesmo comecando por uma. "Oi, onde fica o
# CEMERF?" tem que ir para o RAG.
MAX_PALAVRAS_SAUDACAO = 3


def normalizar(texto: str) -> str:
    """Minusculas, sem acento e sem pontuacao nas bordas."""
    if not texto:
        return ""

    sem_acento = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    return " ".join(sem_acento.casefold().strip(" .,!?;:").split())


def e_saudacao(texto: str) -> bool:
    normalizado = normalizar(texto)

    if not normalizado:
        return False

    if len(normalizado.split()) > MAX_PALAVRAS_SAUDACAO:
        return False

    return normalizado in SAUDACOES
