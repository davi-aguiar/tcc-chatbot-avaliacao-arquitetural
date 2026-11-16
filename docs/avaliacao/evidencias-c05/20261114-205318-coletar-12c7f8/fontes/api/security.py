"""Autenticacao das rotas de entrada.

Modulo proposital sem dependencia de app/ ou dos services: importar isso nao
pode arrastar LangChain nem o indice FAISS, senao os testes ficam impossiveis
de rodar no CI.

Todas as funcoes falham fechado: variavel de ambiente ausente significa negar,
nunca liberar.
"""
import hmac
import os
from typing import Optional

from twilio.request_validator import RequestValidator


def token_webhook_valido(recebido: Optional[str]) -> bool:
    """Compara o token recebido com WEBHOOK_TOKEN.

    Sem a variavel definida, nenhuma requisicao passa: um segredo em branco
    liberaria geral, que e pior do que a rota fora do ar.
    """
    esperado = os.getenv("WEBHOOK_TOKEN", "")

    if not esperado or not recebido:
        return False

    # compare_digest evita vazar o tamanho do prefixo correto por tempo de resposta.
    return hmac.compare_digest(recebido, esperado)


def assinatura_twilio_valida(url: str, params: dict, assinatura: Optional[str]) -> bool:
    """Valida o header X-Twilio-Signature contra o corpo do formulario."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

    if not auth_token or not assinatura:
        return False

    return RequestValidator(auth_token).validate(url, params, assinatura)


def url_publica(url_recebida: str, caminho: str) -> str:
    """URL que a Twilio usou para assinar a requisicao.

    Atras de tunel ou proxy reverso a aplicacao enxerga http://localhost:8000,
    enquanto a Twilio assinou a URL publica em https. Nesse caso a assinatura
    nunca bate, e PUBLIC_BASE_URL corrige.
    """
    base = os.getenv("PUBLIC_BASE_URL", "")

    if base:
        return base.rstrip("/") + caminho

    return url_recebida
