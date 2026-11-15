from fastapi import Header, HTTPException

from api.security import token_webhook_valido

def exigir_token(x_webhook_token: str = Header(default=None)):
    """Protege /messages/receive.

    Sem isso, fechar os dois webhooks nao adianta: esta rota entrega a mesma
    capacidade (falar como qualquer id_wpp e gastar cota da Groq) sem exigir nada.
    """
    if not token_webhook_valido(x_webhook_token):
        raise HTTPException(status_code=403, detail="Token invalido")
