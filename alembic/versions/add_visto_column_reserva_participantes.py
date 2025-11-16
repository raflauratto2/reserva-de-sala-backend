"""add visto column to reserva_participantes

Revision ID: add_visto_column_reserva_participantes
Revises: add_link_meet_column_reservas
Create Date: 2025-01-15 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_visto_col'
down_revision = 'add_link_meet_column_reservas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar coluna visto na tabela reserva_participantes
    op.add_column('reserva_participantes', sa.Column('visto', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    # Remover coluna visto
    op.drop_column('reserva_participantes', 'visto')

