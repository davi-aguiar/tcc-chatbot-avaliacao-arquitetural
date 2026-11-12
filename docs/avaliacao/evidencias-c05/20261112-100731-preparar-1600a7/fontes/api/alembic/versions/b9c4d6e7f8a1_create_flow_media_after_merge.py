"""create_flow_media_after_merge

Revision ID: b9c4d6e7f8a1
Revises: f36d189f393f
Create Date: 2026-04-01 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9c4d6e7f8a1"
down_revision: Union[str, Sequence[str], None] = "f36d189f393f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "flow_media" not in inspector.get_table_names():
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

    result = bind.execute(
        sa.text(
            """
            SELECT id
            FROM flow_media
            WHERE flow_key = :flow_key
              AND media_type = :media_type
              AND media_url = :media_url
            LIMIT 1
            """
        ),
        {
            "flow_key": "CALENDARIO",
            "media_type": "image",
            "media_url": "https://jtqzxjsmynnjurhgurrv.supabase.co/storage/v1/object/public/flow_image.vacinacao/imagem_2026-04-01_121353763.png",
        },
    ).first()

    if not result:
        bind.execute(
            sa.text(
                """
                INSERT INTO flow_media (flow_key, media_type, media_url, caption, is_active, updated_at)
                VALUES (:flow_key, :media_type, :media_url, :caption, :is_active, CURRENT_TIMESTAMP)
                """
            ),
            {
                "flow_key": "CALENDARIO",
                "media_type": "image",
                "media_url": "https://jtqzxjsmynnjurhgurrv.supabase.co/storage/v1/object/public/flow_image.vacinacao/imagem_2026-04-01_121353763.png",
                "caption": None,
                "is_active": True,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "flow_media" in inspector.get_table_names():
        op.drop_index(op.f("ix_flow_media_flow_key"), table_name="flow_media")
        op.drop_table("flow_media")
