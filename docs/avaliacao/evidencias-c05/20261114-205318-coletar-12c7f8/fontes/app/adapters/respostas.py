"""Frase que o RAG devolve quando nao achou a resposta no contexto.

Modulo sem nenhum import de proposito: quem precisa saber "o RAG falhou?" nao
deveria ter que carregar LangChain para descobrir.

O prompt em prompts.py manda o modelo responder exatamente esta frase, e
nlp_service usa a mesma constante para reconhecer o caso. Antes as duas pontas
eram literais soltos, e o ChatService tentava adivinhar a falha procurando
"desculpe" no meio da resposta, o que derrubava resposta boa.
"""

RESPOSTA_SEM_CONTEXTO = (
    "Desculpe, não encontrei essa informação específica nos meus documentos."
)

# O modelo nem sempre devolve a frase caractere a caractere: sobra aspas, ponto
# final a mais, quebra de linha. Casar por este nucleo e mais estavel do que
# exigir igualdade exata, e ainda assim especifico o bastante para nao pegar
# uma resposta legitima.
NUCLEO_SEM_CONTEXTO = "não encontrei essa informação"


def sem_contexto(resposta: str) -> bool:
    """A resposta do RAG e a frase de 'nao encontrei'?"""
    if not resposta or not resposta.strip():
        return True

    return NUCLEO_SEM_CONTEXTO in resposta.casefold()
