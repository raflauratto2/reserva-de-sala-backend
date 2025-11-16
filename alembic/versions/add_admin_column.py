"""add admin column to usuarios

Revision ID: add_admin_column
Revises: 
Create Date: 2025-01-15 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_admin_column'
down_revision = 'create_salas_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar coluna admin na tabela usuarios
    op.add_column('usuarios', sa.Column('admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    # Remover coluna admin
    op.drop_column('usuarios', 'admin')

