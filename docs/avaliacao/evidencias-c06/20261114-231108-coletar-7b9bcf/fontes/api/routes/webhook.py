import logging
import mimetypes
import os

import requests
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.security import token_webhook_valido
from api.services.chat_service import ChatService

router = APIRouter()

logger = logging.getLogger("AppLogger")

EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://localhost:8080")
INSTANCE = os.getenv("EVOLUTION_INSTANCE", "meu-wpp")
API_KEY = os.getenv("EVOLUTION_API_KEY", "")

def send_text(number: str, text: str) -> bool:
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE}"
    try:
        resposta = requests.post(
            url,
            headers={"apikey": API_KEY},
            json={
                "number": number,
                "text": text
            },
            timeout=15
        )
        resposta.raise_for_status()
        return True
    except Exception:
        logger.exception("Falha ao enviar texto para %s", number)
        return False

def send_image(number: str, image_url: str, caption: str = "") -> bool:
    url = f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE}"

    # O mimetype vinha fixo em image/png enquanto a imagem configurada e .jpeg.
    mimetype = mimetypes.guess_type(image_url)[0] or "image/jpeg"
    extensao = mimetypes.guess_extension(mimetype) or ".jpg"

    payload = {
        "number": number,
        "mediatype": "image",
        "mimetype": mimetype,
        "fileName": f"imagem{extensao}",
        "media": image_url,
        "caption": caption
    }

    try:
        resposta = requests.post(
            url,
            headers={
                "apikey": API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )
        resposta.raise_for_status()
        return True
    except Exception:
        logger.exception("Falha ao enviar imagem para %s", number)
        return False

@router.post("/evolution_webhook")
async def evolution_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        # A Evolution API nao assina o payload. O segredo vai na URL configurada
        # no manager (?token=...) ou no header X-Webhook-Token.
        token = request.headers.get("X-Webhook-Token") or request.query_params.get("token")
        if not token_webhook_valido(token):
            return JSONResponse(content={"status": "forbidden"}, status_code=403)

        body = await request.json()

        event_type = body.get("event", "")
        if event_type and "messages.upsert" not in event_type:
             return JSONResponse(content={"status": "ignored", "reason": "not a message event"})
        
        data = body.get("data", {})
        key = data.get("key", {}) if "key" in data else data.get("message", {}).get("key", {})
        remote_jid = key.get("remoteJid", "")
        
        if not remote_jid or "@g.us" in remote_jid or "status@broadcast" in remote_jid:
            return JSONResponse(content={"status": "ignored", "reason": "group or status message"})

        number = remote_jid.split("@")[0]
        
        message_data = data.get("message", {})
        message = message_data.get("conversation") or message_data.get("extendedTextMessage", {}).get("text", "")

        if not message:
            return JSONResponse(content={"status": "no_text"})

        nlp_service = request.app.state.nlp_service
        chat_service = ChatService(db, nlp_service)
        
        resposta = await chat_service.process_message(number, message)

        if resposta.image_url:
            # Imagem falhou: manda ao menos o texto, senao o cidadao fica sem
            # resposta nenhuma e o unico registro e uma linha de log.
            enviado = send_image(number, resposta.image_url, resposta.text)
            if not enviado and resposta.text:
                enviado = send_text(number, resposta.text)
        elif resposta.text:
            enviado = send_text(number, resposta.text)
        else:
            enviado = True

        if not enviado:
            return JSONResponse(
                content={"status": "error", "message": "falha ao entregar a resposta"},
                status_code=502,
            )

        return JSONResponse(content={"status": "success"})

    except Exception as e:
        logger.exception("Falha no evolution_webhook")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)