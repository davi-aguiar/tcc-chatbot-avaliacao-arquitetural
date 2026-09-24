from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


def agora_utc() -> datetime:
    """Hora corrente em UTC, avaliada a cada chamada.

    Existe porque `default=datetime.now(timezone.utc)` passa um *valor*, e nao
    uma funcao: a expressao e avaliada uma unica vez, no import do modulo, e
    toda linha gravada por aquele processo recebe a hora em que a aplicacao
    subiu. Valia para users, chats, messages e audit_logs — todos os created_at
    de um mesmo boot saiam identicos, o que inviabiliza qualquer medicao de
    tempo feita sobre eles e falseia silenciosamente a ordem dos registros.

    Nao se troca por `server_default=func.now()`: no Postgres, now() devolve o
    horario de inicio da *transacao*, e process_message grava a mensagem do
    usuario e a do bot na mesma transacao. As duas voltariam a ter o mesmo
    timestamp — exatamente o que se quer evitar. O equivalente correto no banco
    seria clock_timestamp(), mas ai a hora passa a vir do servidor de banco e
    nao do processo que atende a requisicao, o que mistura dois relogios.
    """
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_wpp = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    state = Column(String, default="NEW") 
    created_at = Column(DateTime, default=agora_utc)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=agora_utc)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    text = Column(String, nullable=False)
    sender = Column(String, nullable=False)  
    created_at = Column(DateTime, default=agora_utc)

    chat = relationship("Chat", back_populates="messages")

class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String, primary_key=True, index=True) 
    value = Column(String, nullable=False)           
    description = Column(String, nullable=True)       
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc)


class FlowMedia(Base):
    __tablename__ = "flow_media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flow_key = Column(String, nullable=False, index=True)
    media_type = Column(String, nullable=False, default="image")
    media_url = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    level = Column(String, nullable=False) 
    event_type = Column(String, nullable=False) 
    message = Column(Text, nullable=False) 
    metadata_info = Column(JSON, nullable=True) 
    created_at = Column(DateTime, default=agora_utc)
