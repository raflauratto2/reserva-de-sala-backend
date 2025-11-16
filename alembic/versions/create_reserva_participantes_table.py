"""create reserva_participantes table

Revision ID: create_reserva_participantes
Revises: add_nome_column_usuarios
Create Date: 2025-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_reserva_participantes'
down_revision = 'add_nome_column_usuarios'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela reserva_participantes
    op.create_table(
        'reserva_participantes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reserva_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('notificado', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['reserva_id'], ['reservas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE')
    )
    op.create_index('ix_reserva_participantes_reserva_id', 'reserva_participantes', ['reserva_id'])
    op.create_index('ix_reserva_participantes_usuario_id', 'reserva_participantes', ['usuario_id'])
    # Constraint única para evitar duplicatas
    op.create_unique_constraint('uq_reserva_usuario', 'reserva_participantes', ['reserva_id', 'usuario_id'])


def downgrade() -> None:
    # Remover tabela reserva_participantes
    op.drop_constraint('uq_reserva_usuario', 'reserva_participantes', type_='unique')
    op.drop_index('ix_reserva_participantes_usuario_id', table_name='reserva_participantes')
    op.drop_index('ix_reserva_participantes_reserva_id', table_name='reserva_participantes')
    op.drop_table('reserva_participantes')

