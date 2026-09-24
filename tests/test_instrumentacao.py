"""Instrumentacao de tempo: created_at por linha e evento MESSAGE_SENT.

Existe para sustentar as medicoes quantitativas do trabalho. Duas delas eram
impossiveis antes:

- `created_at` usava `default=datetime.now(timezone.utc)`, que passa um valor e
  nao uma funcao. Toda linha gravada por um processo recebia a hora do boot, o
  que zera qualquer diferenca de tempo calculada sobre a tabela.
- `audit_logs` so registrava MESSAGE_RECEIVED. Com um unico timestamp por
  mensagem nao ha o que subtrair, e a latencia fim a fim fica inobservavel.

Roda contra sqlite em memoria com os models reais, no mesmo desenho de
test_chat_service.py: o NLPService entra como duble.
"""
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.models.models import AuditLog, Base, Message, SystemConfig, User  # noqa: E402
from api.services.chat_service import ChatService  # noqa: E402

ID = "5577999999999"


class NLPLento:
    """Duble que gasta um tempo conhecido, para a medicao ter o que medir."""

    def __init__(self, atraso_s=0.05, resposta="resposta do RAG"):
        self.atraso_s = atraso_s
        self.resposta = resposta
        self.perguntas = []

    def process(self, text, user_name=None):
        self.perguntas.append(text)
        time.sleep(self.atraso_s)
        return self.resposta


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine)()
    yield sessao
    sessao.close()


@pytest.fixture
def nlp():
    return NLPLento()


def conversa(db, nlp):
    def mandar(texto, id_wpp=ID):
        service = ChatService(db, nlp)
        return asyncio.run(service.process_message(id_wpp, texto))
    return mandar


def agora_naive():
    """UTC sem tzinfo: e assim que o valor volta das colunas DateTime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def eventos(db, event_type):
    return (
        db.query(AuditLog)
        .filter(AuditLog.event_type == event_type)
        .order_by(AuditLog.id)
        .all()
    )


# --- created_at avaliado por linha ------------------------------------------

def test_created_at_reflete_o_momento_da_insercao(db):
    antes = agora_naive()
    time.sleep(0.02)

    user = User(id_wpp=ID, state="NEW")
    db.add(user)
    db.commit()

    time.sleep(0.02)
    depois = agora_naive()

    # O defeito antigo gravava a hora do import do modulo, sempre anterior a
    # `antes`. Esta faixa e o que separa "hora da insercao" de "hora do boot".
    assert antes < user.created_at < depois


def test_linhas_gravadas_em_momentos_diferentes_tem_created_at_diferente(db):
    primeira = Message(chat_id=1, text="a", sender="user")
    db.add(primeira)
    db.commit()

    time.sleep(0.02)

    segunda = Message(chat_id=1, text="b", sender="bot")
    db.add(segunda)
    db.commit()

    assert primeira.created_at != segunda.created_at
    assert segunda.created_at > primeira.created_at


def test_updated_at_avanca_quando_a_linha_muda(db):
    config = SystemConfig(key="maintenance_mode", value="false")
    db.add(config)
    db.commit()
    primeiro = config.updated_at

    time.sleep(0.02)
    config.value = "true"
    db.commit()

    # onupdate sofria do mesmo defeito de default: valor congelado no import.
    assert config.updated_at > primeiro


# --- MESSAGE_SENT ------------------------------------------------------------

def test_message_sent_registrado_a_cada_resposta(db, nlp):
    mandar = conversa(db, nlp)

    mandar("oi")
    mandar("Maria")

    assert len(eventos(db, "MESSAGE_SENT")) == 2


def test_par_recebido_enviado_permite_calcular_latencia(db, nlp):
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")
    mandar("2")
    mandar("1")  # opcao com query: passa pelo RAG

    recebido = eventos(db, "MESSAGE_RECEIVED")[-1]
    enviado = eventos(db, "MESSAGE_SENT")[-1]

    assert enviado.created_at >= recebido.created_at
    assert enviado.metadata_info["duracao_total_ms"] > 0


def test_duracao_rag_medida_na_opcao_de_menu(db, nlp):
    """Caminho que o envelope de cronometragem existe para cobrir.

    Opcao de menu com `query` chama o NLPService de dentro de
    handle_dynamic_menu, sem passar por _perguntar_ao_rag.
    """
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")
    mandar("2")
    mandar("1")

    meta = eventos(db, "MESSAGE_SENT")[-1].metadata_info

    assert meta["chamou_rag"] is True
    assert meta["chamadas_rag"] == 1
    # O duble dorme 50 ms; a medicao tem de enxergar isso.
    assert meta["duracao_rag_ms"] >= 45
    assert meta["duracao_total_ms"] >= meta["duracao_rag_ms"]


def test_duracao_rag_medida_no_texto_livre(db, nlp):
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")
    mandar("onde fica o CEMERF?")

    meta = eventos(db, "MESSAGE_SENT")[-1].metadata_info

    assert meta["chamou_rag"] is True
    assert meta["duracao_rag_ms"] >= 45


def test_navegacao_de_menu_nao_reporta_duracao_de_rag(db, nlp):
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")
    mandar("2")  # so troca de estado, sem RAG

    meta = eventos(db, "MESSAGE_SENT")[-1].metadata_info

    assert meta["chamou_rag"] is False
    # Ausente, e nao zero: "nao chamou" e "chamou e levou 0 ms" sao coisas
    # diferentes na hora de tirar a media da latencia do RAG.
    assert "duracao_rag_ms" not in meta


def test_estados_de_entrada_e_saida_ficam_no_log(db, nlp):
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")

    meta = eventos(db, "MESSAGE_SENT")[-1].metadata_info

    assert meta["estado_entrada"] == "WAITING_NAME"
    assert meta["estado_saida"] == "WAITING_MAIN_MENU"


def test_log_nao_carrega_o_texto_da_conversa(db, nlp):
    """Minimizacao: audit_logs nao duplica o que o cidadao escreveu.

    A conversa ja esta inteira em `messages`. Repeti-la aqui espalharia dado de
    saude por mais uma tabela sem finalidade propria.
    """
    pergunta = "tenho dor no peito e preciso de cardiologista"
    mandar = conversa(db, nlp)
    mandar("oi")
    mandar("Maria")
    mandar(pergunta)

    enviado = eventos(db, "MESSAGE_SENT")[-1]
    serializado = json.dumps(enviado.metadata_info, ensure_ascii=False)

    assert pergunta not in serializado
    assert "dor no peito" not in serializado
    assert nlp.resposta not in serializado
    # Grandeza sim, conteudo nao.
    assert enviado.metadata_info["tamanho_resposta"] > 0
