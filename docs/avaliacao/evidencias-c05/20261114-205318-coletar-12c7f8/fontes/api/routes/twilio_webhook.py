from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from xml.sax.saxutils import escape

from api.db.database import get_db
from api.security import assinatura_twilio_valida, url_publica
from api.services.chat_service import ChatService

router = APIRouter()


@router.post("/twilio/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    if not assinatura_twilio_valida(
        url_publica(str(request.url), request.url.path),
        dict(form),
        request.headers.get("X-Twilio-Signature"),
    ):
        raise HTTPException(status_code=403, detail="Assinatura Twilio invalida")

    text = form.get("Body", "")
    id_wpp = form.get("From", "")

    nlp_service = request.app.state.nlp_service
    chat_service = ChatService(db, nlp_service)
    resposta = await chat_service.process_message(id_wpp, text)

    safe_text = escape(resposta.text)
    media_xml = ""

    if resposta.image_url:
        media_xml = f"\n        <Media>{escape(resposta.image_url)}</Media>"

    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>{safe_text}</Body>{media_xml}
    </Message>
</Response>"""

    return PlainTextResponse(xml_response, media_type="application/xml")
