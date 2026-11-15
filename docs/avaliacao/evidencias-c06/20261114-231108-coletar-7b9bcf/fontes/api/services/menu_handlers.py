import json
import os
from typing import Optional

from api.schemas.responses import ChatResponse
from api.services.config_service import ConfigService
from api.services.flow_media_service import FlowMediaService

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_json = os.path.join(diretorio_atual, "menu_texts.json")

with open(caminho_json, "r", encoding="utf-8") as file:
    TEXTS = json.load(file)

def build_response(text: str, image_key: Optional[str] = None, db=None) -> ChatResponse:
    image_url = None
    if image_key:
        image_url = _resolve_image_url(image_key, db=db)
    return ChatResponse(text=text, image_url=image_url)

def _resolve_image_url(image_key: str, db=None) -> Optional[str]:
    if db is not None:
        flow_media_value = FlowMediaService(db).get_active_image_url(image_key)
        if flow_media_value:
            return flow_media_value

        config_value = ConfigService(db).get_flow_image_url(image_key)
        if config_value:
            return config_value

    env_value = os.getenv(f"FLOW_IMAGE_{image_key.upper()}")
    if env_value:
        return env_value

    return TEXTS.get("FLOW_IMAGE_URLS", {}).get(image_key) or None

def handle_dynamic_menu(user, choice: str, nlp_service, db) -> ChatResponse:
    if not user.state or user.state not in TEXTS:
        user.state = "WAITING_MAIN_MENU"
        if choice not in TEXTS["WAITING_MAIN_MENU"]["options"]:
            return build_response(TEXTS["WAITING_MAIN_MENU"]["text"], db=db)

    current_state_data = TEXTS[user.state]
    option_config = current_state_data["options"].get(choice)

    if not option_config:
        return build_response(f"⚠️ Opção inválida. Por favor, escolha uma das opções válidas:\n\n{current_state_data['text']}", db=db)

    image_key = option_config.get("image_key")

    if "next_state" in option_config:
        next_state = option_config["next_state"]
        user.state = next_state
        return build_response(TEXTS[next_state]["text"], image_key=image_key, db=db)

    elif "query" in option_config:
        query = option_config["query"]

        rag_answer = nlp_service.process(query, user_name=user.name)

        if rag_answer:
            texto_final = f"{rag_answer}\n\n*(Escolha outra opção do menu ou digite 0 para voltar ao início)*"
        else:
            texto_final = "Desculpe, não encontrei essa informação nos documentos.\n\n*(Escolha outra opção do menu ou digite 0 para voltar ao início)*"

        return build_response(
            texto_final,
            image_key=image_key,
            db=db
        )

    return build_response("Ocorreu um erro ao processar sua opção. Digite 0 para voltar.", db=db)