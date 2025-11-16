"""add nome column to usuarios

Revision ID: add_nome_column_usuarios
Revises: add_admin_column
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_nome_column_usuarios'
down_revision = 'add_admin_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar coluna nome na tabela usuarios
    op.add_column('usuarios', sa.Column('nome', sa.String(), nullable=True))


def downgrade() -> None:
    # Remover coluna nome
    op.drop_column('usuarios', 'nome')

