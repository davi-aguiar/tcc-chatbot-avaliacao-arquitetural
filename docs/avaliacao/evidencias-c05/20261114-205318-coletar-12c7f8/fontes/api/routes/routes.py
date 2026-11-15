from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from api.schemas.schemas import MessageSchema, MessageOut
from api.db.database import get_db
from api.dependencies.dependencies import exigir_token
from api.services.chat_service import ChatService

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/receive", response_model=MessageOut, dependencies=[Depends(exigir_token)])
async def receive_message(
    payload: MessageSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    nlp_service = request.app.state.nlp_service

    service = ChatService(db, nlp_service)
    response = await service.process_message(payload.id_wpp, payload.text)

    return MessageOut(response=response.text, image_url=response.image_url)
