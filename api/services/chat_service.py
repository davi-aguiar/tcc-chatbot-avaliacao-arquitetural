import logging
import time
from typing import TYPE_CHECKING, Optional

from api.models.models import User, Chat, Message
from api.schemas.responses import ChatResponse
from api.utils.logger import DbLogger
from api.services.config_service import ConfigService

from api.services.menu_handlers import handle_dynamic_menu, TEXTS

if TYPE_CHECKING:  # pragma: no cover
    # Import so em tempo de tipagem: NLPService arrasta LangChain e o modelo de
    # embeddings, o que tiraria a maquina de estados do alcance dos testes.
    from api.services.nlp_service import NLPService

logger = logging.getLogger("AppLogger")

COMANDOS_MENU = ("menu", "/menu")
COMANDO_RESETAR = "/resetar"

APRESENTACAO = "Olá! Sou o assistente virtual da Secretaria Municipal de Saúde."


def normalizar_id_wpp(id_wpp: str) -> str:
    """Reduz o identificador ao numero, seja qual for o gateway.

    A Twilio entrega "whatsapp:+5577999999999" e a Evolution API entrega
    "5577999999999". Sem normalizar, o mesmo cidadao vira dois usuarios com
    estados independentes.
    """
    return "".join(c for c in (id_wpp or "") if c.isdigit())


class _NLPCronometrado:
    """Envelope que cronometra cada chamada ao RAG.

    Existe porque ha dois caminhos ate o NLPService: texto livre passa por
    `_perguntar_ao_rag`, mas opcao de menu com `query` chama o servico direto,
    de dentro de `handle_dynamic_menu`. Medir so no primeiro deixaria de fora a
    maior parte do trafego — quase todo o menu responde por query de RAG.

    Acumula em vez de sobrescrever: uma mensagem pode, em tese, disparar mais de
    uma chamada, e nesse caso a soma e o que interessa para a latencia.
    """

    def __init__(self, nlp):
        self._nlp = nlp
        self.duracao_ms = 0.0
        self.chamadas = 0

    def process(self, text, user_name=None):
        inicio = time.perf_counter()
        try:
            return self._nlp.process(text, user_name=user_name)
        finally:
            # finally, e nao depois do return: chamada que levanta excecao
            # tambem consumiu tempo, e e justamente o caso lento (timeout da
            # Groq) que mais interessa medir.
            self.duracao_ms += (time.perf_counter() - inicio) * 1000
            self.chamadas += 1


class ChatService:
    def __init__(self, db, nlp_service: "NLPService"):
        self.db = db
        self.nlp = _NLPCronometrado(nlp_service)
        self.config_service = ConfigService(db)

    async def process_message(self, id_wpp: str, text: str) -> ChatResponse:
        # Marcado antes de qualquer trabalho: o que se quer medir e o tempo de
        # processamento inteiro, nao o trecho depois das validacoes.
        inicio = time.perf_counter()

        # Guardado a parte: depois de um rollback, tocar no objeto User pode
        # disparar refresh e estourar de novo dentro do proprio except.
        user_id = None
        try:
            text = (text or "").strip()

            if not text:
                return ChatResponse(text="Não entendi sua mensagem. Pode repetir?")

            clean_text = self._clean_text(text)

            user = self._get_or_create_user(id_wpp)
            user_id = user.id
            estado_entrada = user.state
            chat = self._get_or_create_chat(user)

            DbLogger.log_event(
                self.db,
                "INFO",
                "MESSAGE_RECEIVED",
                f"Mensagem recebida de {user.id_wpp}",
                user_id=user.id
            )

            self._save_message(chat, text, "user")

            response = self._responder(user, clean_text)
            response = self._ensure_chat_response(response)

            self._save_message(chat, response.text, "bot")

            # Lidos antes do commit: depois dele os atributos do User expiram e
            # cada leitura dispara um SELECT de refresh so para montar o log.
            id_wpp_log, estado_saida = user.id_wpp, user.state

            self.db.commit()

            self._registrar_envio(
                user_id=user_id,
                id_wpp=id_wpp_log,
                estado_entrada=estado_entrada,
                estado_saida=estado_saida,
                response=response,
                inicio=inicio,
            )

            return response

        except Exception as e:
            self.db.rollback()
            logger.exception("Falha ao processar mensagem de %s", id_wpp)
            DbLogger.log_event(
                self.db,
                "ERROR",
                "MESSAGE_FAILED",
                f"Falha ao processar mensagem: {e}",
                user_id=user_id,
                meta={
                    "id_wpp": id_wpp,
                    "erro": type(e).__name__,
                    "duracao_total_ms": self._ms_desde(inicio),
                    "duracao_rag_ms": self._ms_rag(),
                },
            )
            return ChatResponse(text="Desculpe, ocorreu um erro interno.")

    def _registrar_envio(
        self,
        user_id: Optional[int],
        id_wpp: str,
        estado_entrada: Optional[str],
        estado_saida: Optional[str],
        response: ChatResponse,
        inicio: float,
    ) -> None:
        """Fecha o par com MESSAGE_RECEIVED.

        Sem este evento existe um unico timestamp por mensagem e a latencia
        fim a fim fica inobservavel: nao ha o que subtrair. Registrar o tempo
        aqui, e nao no gateway, mede exatamente o trecho sob responsabilidade
        da aplicacao — recepcao, decisao, RAG, persistencia e commit.

        O texto da pergunta e o da resposta ficam de fora do meta de proposito.
        audit_logs e tabela de operacao e a conversa ja esta inteira em
        `messages`; repetir aqui o que o cidadao escreveu duplicaria dado de
        saude em mais um lugar, sem finalidade propria, contra o principio de
        minimizacao da LGPD. Vao so grandezas: duracao, estado e tamanho.
        """
        meta = {
            "duracao_total_ms": self._ms_desde(inicio),
            "estado_entrada": estado_entrada,
            "estado_saida": estado_saida,
            "chamou_rag": self.nlp.chamadas > 0,
            "chamadas_rag": self.nlp.chamadas,
            "tem_imagem": bool(response.image_url),
            "tamanho_resposta": len(response.text or ""),
        }

        duracao_rag = self._ms_rag()
        if duracao_rag is not None:
            meta["duracao_rag_ms"] = duracao_rag

        DbLogger.log_event(
            self.db,
            "INFO",
            "MESSAGE_SENT",
            f"Resposta enviada para {id_wpp}",
            user_id=user_id,
            meta=meta,
        )

    @staticmethod
    def _ms_desde(inicio: float) -> float:
        # perf_counter e nao datetime.now(): relogio monotonico, imune a ajuste
        # de horario (NTP) no meio da requisicao, que produziria duracao
        # negativa ou inflada justamente sob carga.
        return round((time.perf_counter() - inicio) * 1000, 2)

    def _ms_rag(self) -> Optional[float]:
        """None quando o RAG nao foi acionado — menu puro, onboarding, reset.

        Distinguir 'nao chamou' de 'chamou e levou 0 ms' importa: a media de
        latencia do RAG so faz sentido sobre as mensagens que passaram por ele.
        """
        if not self.nlp.chamadas:
            return None
        return round(self.nlp.duracao_ms, 2)

    def _responder(self, user: User, clean_text: str) -> ChatResponse:
        if clean_text.lower() == COMANDO_RESETAR:
            return self._resetar(user)

        if not user.state:
            user.state = "NEW"
        elif user.state not in ("NEW", "WAITING_NAME") and user.state not in TEXTS:
            user.state = "WAITING_MAIN_MENU"

        if clean_text.lower() in COMANDOS_MENU:
            return self._voltar_ao_menu(user)

        if user.state == "NEW":
            return self._primeiro_contato(user, clean_text)

        if user.state == "WAITING_NAME":
            return self._registrar_nome(user, clean_text)

        return self._dentro_do_menu(user, clean_text)

    def _resetar(self, user: User) -> ChatResponse:
        # Limpar o nome junto: mantendo-o, o ramo NEW pula o onboarding e o
        # usuario nunca consegue corrigir um nome digitado errado.
        user.state = "NEW"
        user.name = None
        return ChatResponse(
            text="Conversa reiniciada!\nEnvie uma mensagem para começar."
        )

    def _voltar_ao_menu(self, user: User) -> ChatResponse:
        if not user.name:
            user.state = "WAITING_NAME"
            return ChatResponse(
                text=f"{APRESENTACAO}\nPara acessar o menu, digite apenas o seu nome:"
            )

        user.state = "WAITING_MAIN_MENU"
        return ChatResponse(
            text=f"Voltando ao menu principal...\n\n{TEXTS['WAITING_MAIN_MENU']['text']}"
        )

    def _primeiro_contato(self, user: User, clean_text: str) -> ChatResponse:
        if not user.name:
            user.state = "WAITING_NAME"
            return ChatResponse(
                text=f"{APRESENTACAO}\nPara continuar, digite apenas o seu nome:"
            )

        user.state = "WAITING_MAIN_MENU"
        rag_response = self._perguntar_ao_rag(clean_text, user.name) or f"Oi, {user.name}!"
        return ChatResponse(
            text=f"{rag_response}\n\n{TEXTS['WAITING_MAIN_MENU']['text']}"
        )

    def _registrar_nome(self, user: User, clean_text: str) -> ChatResponse:
        nome = self._extract_name(clean_text)

        if len(nome) < 2:
            return ChatResponse(text="Digite um nome válido.")
        if len(nome) > 30:
            return ChatResponse(text="Nome muito longo. Digite apenas seu primeiro nome.")
        if any(char.isdigit() for char in nome):
            return ChatResponse(text="O nome não deve conter números.")
        if len(nome.split()) > 3:
            return ChatResponse(text="Digite apenas seu primeiro nome.")

        user.name = nome
        user.state = "WAITING_MAIN_MENU"
        return ChatResponse(
            text=(
                f"Prazer, {user.name}! 😊\n"
                "Como posso te ajudar hoje?\n\n"
                f"{TEXTS['WAITING_MAIN_MENU']['text']}"
            )
        )

    def _dentro_do_menu(self, user: User, clean_text: str) -> ChatResponse:
        state_config = TEXTS[user.state]
        current_menu_text = state_config["text"]

        if state_config.get("options", {}).get(clean_text):
            return handle_dynamic_menu(user, clean_text, self.nlp, self.db)

        if clean_text.isdigit():
            return self._opcao_invalida(current_menu_text)

        if self._em_manutencao():
            return ChatResponse(text="O Chat Bot está em manutenção.")

        rag_response = self._perguntar_ao_rag(clean_text, user.name)

        if not rag_response:
            return self._opcao_invalida(current_menu_text)

        return ChatResponse(text=f"{rag_response}\n\n{current_menu_text}")

    def _opcao_invalida(self, menu_text: str) -> ChatResponse:
        return ChatResponse(
            text=f"Opção inválida. Por favor, digite um número válido:\n\n{menu_text}"
        )

    def _em_manutencao(self) -> bool:
        return self.config_service.get_config("maintenance_mode", "false") == "true"

    def _perguntar_ao_rag(self, texto: str, user_name: Optional[str]) -> Optional[str]:
        """None quando o RAG nao achou resposta ou quando ele explodiu.

        NLPService.process ja devolve None para 'nao encontrei no contexto', o
        que dispensa procurar palavras de erro dentro da resposta.
        """
        try:
            return self.nlp.process(texto, user_name=user_name)
        except Exception:
            logger.exception("NLPService falhou para: %r", texto)
            return None

    def _ensure_chat_response(self, response) -> ChatResponse:
        if isinstance(response, ChatResponse):
            return response
        return ChatResponse(text=str(response))

    def _clean_text(self, text: str) -> str:
        # Antes isto cortava tudo antes do ultimo ":", para remover prefixo de
        # gateway. Efeito colateral: "Horário: 8 às 17" virava "8 às 17".
        # Prefixo de gateway, se voltar, e problema da rota, nao do dominio.
        return " ".join((text or "").strip().split())

    def _extract_name(self, text: str) -> str:
        return self._clean_text(text)

    def _get_or_create_user(self, id_wpp: str) -> User:
        id_wpp = normalizar_id_wpp(id_wpp) or id_wpp
        user = self.db.query(User).filter(User.id_wpp == id_wpp).first()
        if not user:
            user = User(id_wpp=id_wpp, state="NEW")
            self.db.add(user)
            self.db.flush()
        return user

    def _get_or_create_chat(self, user: User) -> Chat:
        chat = self.db.query(Chat).filter(Chat.user_id == user.id).first()
        if not chat:
            chat = Chat(user=user)
            self.db.add(chat)
            self.db.flush()
        return chat

    def _save_message(self, chat: Chat, text: str, sender: str) -> Message:
        message = Message(chat=chat, text=str(text), sender=sender)
        self.db.add(message)
        self.db.flush()
        return message
