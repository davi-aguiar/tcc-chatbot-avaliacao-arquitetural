"""flow_media_table

Revision ID: a8f3b1c2d4e5
Revises: 725740865e73
Create Date: 2026-04-01 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8f3b1c2d4e5"
down_revision: Union[str, Sequence[str], None] = "725740865e73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "flow_media",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flow_key", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("media_url", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flow_media_flow_key"), "flow_media", ["flow_key"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO flow_media (flow_key, media_type, media_url, caption, is_active, updated_at)
            VALUES (:flow_key, :media_type, :media_url, :caption, :is_active, CURRENT_TIMESTAMP)
            """
        ).bindparams(
            flow_key="CALENDARIO",
            media_type="image",
            media_url="https://jtqzxjsmynnjurhgurrv.supabase.co/storage/v1/object/public/flow_image.vacinacao/imagem_2026-04-01_121353763.png",
            caption=None,
            is_active=True,
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_flow_media_flow_key"), table_name="flow_media")
    op.drop_table("flow_media")
