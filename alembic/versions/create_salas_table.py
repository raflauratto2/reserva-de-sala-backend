"""create salas table and update reservas

Revision ID: create_salas_table
Revises: ab20a58fc9c5
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_salas_table'
down_revision = 'ab20a58fc9c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela salas
    op.create_table('salas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('local', sa.String(), nullable=False),
    sa.Column('capacidade', sa.Integer(), nullable=True),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('criador_id', sa.Integer(), nullable=False),
    sa.Column('ativa', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['criador_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salas_id'), 'salas', ['id'], unique=False)
    op.create_index(op.f('ix_salas_nome'), 'salas', ['nome'], unique=False)
    
    # Atualizar tabela reservas: tornar local e sala nullable e adicionar sala_id
    op.alter_column('reservas', 'local',
                   existing_type=sa.String(),
                   nullable=True)
    op.alter_column('reservas', 'sala',
                   existing_type=sa.String(),
                   nullable=True)
    op.add_column('reservas', sa.Column('sala_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_reservas_sala_id', 'reservas', 'salas', ['sala_id'], ['id'])


def downgrade() -> None:
    # Remover foreign key e coluna sala_id de reservas
    op.drop_constraint('fk_reservas_sala_id', 'reservas', type_='foreignkey')
    op.drop_column('reservas', 'sala_id')
    
    # Reverter alterações nas colunas local e sala
    op.alter_column('reservas', 'sala',
                   existing_type=sa.String(),
                   nullable=False)
    op.alter_column('reservas', 'local',
                   existing_type=sa.String(),
                   nullable=False)
    
    # Remover tabela salas
    op.drop_index(op.f('ix_salas_nome'), table_name='salas')
    op.drop_index(op.f('ix_salas_id'), table_name='salas')
    op.drop_table('salas')

