from fastapi import FastAPI
from api.routes.routes import router
from api.routes.twilio_webhook import router as twilio_router
from api.routes.webhook import router as webhook_router
from app.main import setup_system
from api.services.nlp_service import NLPService

app = FastAPI()

pln_resources = setup_system()

app.state.nlp_service = NLPService(
    retriever=pln_resources["servicos"]
)

app.include_router(router)
app.include_router(twilio_router) 
app.include_router(webhook_router)