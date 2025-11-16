"""add link_meet column to reservas

Revision ID: add_link_meet_column_reservas
Revises: create_reserva_participantes
Create Date: 2025-01-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_link_meet_column_reservas'
down_revision = 'create_reserva_participantes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar coluna link_meet na tabela reservas
    op.add_column('reservas', sa.Column('link_meet', sa.String(), nullable=True))


def downgrade() -> None:
    # Remover coluna link_meet
    op.drop_column('reservas', 'link_meet')

