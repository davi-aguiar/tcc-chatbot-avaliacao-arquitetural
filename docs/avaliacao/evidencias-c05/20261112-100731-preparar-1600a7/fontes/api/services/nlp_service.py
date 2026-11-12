from typing import Optional

from app.adapters.respostas import sem_contexto
from app.core.rag_pipeline import run_rag

SAUDACAO_INSTITUCIONAL = (
    "Olá! Sou o assistente virtual da Secretaria Municipal de Saúde de Vitória da Conquista"
)


class NLPService:
    def __init__(self, retriever):
        self.retriever = retriever

    def process(self, text: str, user_name: str = None) -> Optional[str]:
        """Resposta do RAG, ou None quando ele nao achou nada no contexto.

        Devolver None em vez da frase de erro tira do chamador a tarefa de
        adivinhar se a IA falhou procurando palavras no meio do texto.
        """
        if not text or not text.strip():
            return None

        rag_response = run_rag(retriever=self.retriever, question=text)

        if sem_contexto(rag_response):
            return None

        if user_name:
            rag_response = self._personalizar(rag_response, user_name)

        return rag_response

    def _personalizar(self, resposta: str, user_name: str) -> str:
        if SAUDACAO_INSTITUCIONAL in resposta:
            return f"Oi, {user_name}! 😊\nComo posso te ajudar?"

        if "Olá!" in resposta:
            return resposta.replace("Olá!", f"Oi, {user_name}! 😊")

        return resposta
