"""normaliza_id_wpp

Reduz users.id_wpp ao numero puro.

A Twilio grava "whatsapp:+5577999999999" e a Evolution API grava
"5577999999999". Sem isso, o mesmo cidadao existe duas vezes, com nome e
estado separados, e a normalizacao no ChatService deixaria os registros
antigos orfaos.

Revision ID: d2f3a4b5c6d7
Revises: c7d8e9fa0b1c
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "c7d8e9fa0b1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _so_digitos(valor: str) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


def normalizar_usuarios(bind) -> None:
    """Separado de upgrade() para caber num teste sem contexto do Alembic."""
    linhas = bind.execute(sa.text("SELECT id, id_wpp FROM users")).fetchall()

    ocupados = {linha.id_wpp for linha in linhas}

    for linha in linhas:
        normalizado = _so_digitos(linha.id_wpp)

        if not normalizado or normalizado == linha.id_wpp:
            continue

        # Ja existe usuario com o numero puro (mesma pessoa pelos dois
        # gateways). Fundir historico exigiria decidir qual nome e estado
        # sobrevivem, entao a linha antiga fica como esta e simplesmente para
        # de receber mensagens. id_wpp e UNIQUE: sem esta guarda, a migracao
        # quebraria no meio.
        if normalizado in ocupados:
            continue

        bind.execute(
            sa.text("UPDATE users SET id_wpp = :novo WHERE id = :id"),
            {"novo": normalizado, "id": linha.id},
        )
        ocupados.discard(linha.id_wpp)
        ocupados.add(normalizado)


def upgrade() -> None:
    # Normalizacao em Python, nao em SQL: extrair digitos de forma portavel
    # entre Postgres e sqlite daria uma expressao ilegivel.
    normalizar_usuarios(op.get_bind())


def downgrade() -> None:
    # O prefixo original nao e recuperavel: "5577..." nao diz se veio como
    # "whatsapp:+5577..." ou puro. Reverter e no-op de proposito.
    pass
