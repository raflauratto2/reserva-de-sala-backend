from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import Optional, List

from app.models import Reserva
from app.views import ReservaCreate, ReservaUpdate, ReservaResponse
from app.exceptions import ConflitoHorarioException


class ReservaController:
    """Controller para gerenciar reservas."""
    
    @staticmethod
    def verificar_conflito_horario(
        db: Session,
        sala: str,
        data_hora_inicio: datetime,
        data_hora_fim: datetime,
        reserva_id_excluir: Optional[int] = None
    ) -> bool:
        """
        Verifica se existe conflito de horário para uma sala.
        Retorna True se houver conflito, False caso contrário.
        """
        query = db.query(Reserva).filter(
            Reserva.sala == sala,
            or_(
                and_(
                    Reserva.data_hora_inicio <= data_hora_inicio,
                    Reserva.data_hora_fim > data_hora_inicio
                ),
                and_(
                    Reserva.data_hora_inicio < data_hora_fim,
                    Reserva.data_hora_fim >= data_hora_fim
                ),
                and_(
                    Reserva.data_hora_inicio >= data_hora_inicio,
                    Reserva.data_hora_fim <= data_hora_fim
                )
            )
        )
        
        if reserva_id_excluir:
            query = query.filter(Reserva.id != reserva_id_excluir)
        
        return query.first() is not None

    @staticmethod
    def criar(db: Session, reserva: ReservaCreate, responsavel_id: int) -> Reserva:
        """Cria uma nova reserva validando conflitos de horário."""
        if reserva.data_hora_fim <= reserva.data_hora_inicio:
            raise ValueError("A data/hora de fim deve ser maior que a data/hora de início")
        
        if ReservaController.verificar_conflito_horario(
            db, reserva.sala, reserva.data_hora_inicio, reserva.data_hora_fim
        ):
            raise ConflitoHorarioException(
                f"Já existe uma reserva para a sala '{reserva.sala}' no horário especificado"
            )
        
        db_reserva = Reserva(
            **reserva.model_dump(),
            responsavel_id=responsavel_id
        )
        db.add(db_reserva)
        db.commit()
        db.refresh(db_reserva)
        return db_reserva

    @staticmethod
    def obter_por_id(db: Session, reserva_id: int) -> Optional[Reserva]:
        """Obtém uma reserva por ID."""
        return db.query(Reserva).filter(Reserva.id == reserva_id).first()

    @staticmethod
    def listar(db: Session, skip: int = 0, limit: int = 100) -> List[Reserva]:
        """Lista todas as reservas."""
        return db.query(Reserva).offset(skip).limit(limit).all()

    @staticmethod
    def atualizar(
        db: Session,
        reserva_id: int,
        reserva_update: ReservaUpdate,
        responsavel_id: int
    ) -> Optional[Reserva]:
        """Atualiza uma reserva validando conflitos de horário."""
        db_reserva = ReservaController.obter_por_id(db, reserva_id)
        if not db_reserva:
            return None
        
        # Verifica se o responsável é o dono da reserva
        if db_reserva.responsavel_id != responsavel_id:
            return None
        
        update_data = reserva_update.model_dump(exclude_unset=True)
        
        # Se está atualizando horário ou sala, verifica conflitos
        if "data_hora_inicio" in update_data or "data_hora_fim" in update_data or "sala" in update_data:
            nova_sala = update_data.get("sala", db_reserva.sala)
            nova_inicio = update_data.get("data_hora_inicio", db_reserva.data_hora_inicio)
            nova_fim = update_data.get("data_hora_fim", db_reserva.data_hora_fim)
            
            if nova_fim <= nova_inicio:
                raise ValueError("A data/hora de fim deve ser maior que a data/hora de início")
            
            if ReservaController.verificar_conflito_horario(db, nova_sala, nova_inicio, nova_fim, reserva_id):
                raise ConflitoHorarioException(
                    f"Já existe uma reserva para a sala '{nova_sala}' no horário especificado"
                )
        
        for field, value in update_data.items():
            setattr(db_reserva, field, value)
        
        db.commit()
        db.refresh(db_reserva)
        return db_reserva

    @staticmethod
    def deletar(db: Session, reserva_id: int, responsavel_id: int) -> bool:
        """Deleta uma reserva."""
        db_reserva = ReservaController.obter_por_id(db, reserva_id)
        if not db_reserva:
            return False
        
        # Verifica se o responsável é o dono da reserva
        if db_reserva.responsavel_id != responsavel_id:
            return False
        
        db.delete(db_reserva)
        db.commit()
        return True



