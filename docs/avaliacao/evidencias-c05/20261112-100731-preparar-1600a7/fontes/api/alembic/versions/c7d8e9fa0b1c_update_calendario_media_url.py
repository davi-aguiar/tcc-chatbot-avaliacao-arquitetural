"""update_calendario_media_url

Atualiza o seed de CALENDARIO para a URL vigente do Supabase.

O seed inserido por a8f3b1c2d4e5 aponta para o projeto antigo
(jtqzxjsmynnjurhgurrv). O commit c10f74e trocou a URL em menu_texts.json, mas
esse arquivo e o ultimo nivel da cascata de resolucao: a linha em flow_media
vence, entao todo banco ja migrado continuou servindo a imagem antiga.

Revision ID: c7d8e9fa0b1c
Revises: b9c4d6e7f8a1
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9fa0b1c"
down_revision: Union[str, Sequence[str], None] = "b9c4d6e7f8a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

URL_ANTIGA = (
    "https://jtqzxjsmynnjurhgurrv.supabase.co/storage/v1/object/public"
    "/flow_image.vacinacao/imagem_2026-04-01_121353763.png"
)
URL_ATUAL = (
    "https://vfnrmghzyxkpdcvlonjt.supabase.co/storage/v1/object/public"
    "/flow_image.vacinacao/vacinacao.jpeg"
)

SQL = sa.text(
    """
    UPDATE flow_media
       SET media_url = :destino,
           updated_at = CURRENT_TIMESTAMP
     WHERE flow_key = 'CALENDARIO'
       AND media_type = 'image'
       AND media_url = :origem
    """
)


def upgrade() -> None:
    # Filtrar por media_url preserva qualquer URL que tenha sido ajustada a mao
    # direto no banco depois da migracao original.
    op.get_bind().execute(SQL.bindparams(origem=URL_ANTIGA, destino=URL_ATUAL))


def downgrade() -> None:
    op.get_bind().execute(SQL.bindparams(origem=URL_ATUAL, destino=URL_ANTIGA))
