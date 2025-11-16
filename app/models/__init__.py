from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=True)  # Nome completo do usuário
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reservas = relationship("Reserva", back_populates="responsavel")
    salas_criadas = relationship("Sala", back_populates="criador")


class Sala(Base):
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    local = Column(String, nullable=False)
    capacidade = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)
    criador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    criador = relationship("Usuario", back_populates="salas_criadas")
    reservas = relationship("Reserva", back_populates="sala_rel")


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    local = Column(String, nullable=True)  # Mantido para compatibilidade, pode ser removido depois
    sala = Column(String, nullable=True)  # Mantido para compatibilidade, pode ser removido depois
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=True)  # Nova FK para Sala
    data_hora_inicio = Column(DateTime, nullable=False)
    data_hora_fim = Column(DateTime, nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cafe_quantidade = Column(Integer, nullable=True)
    cafe_descricao = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    responsavel = relationship("Usuario", back_populates="reservas")
    sala_rel = relationship("Sala", back_populates="reservas")

    __table_args__ = (
        CheckConstraint('data_hora_fim > data_hora_inicio', name='check_data_hora_valida'),
    )

