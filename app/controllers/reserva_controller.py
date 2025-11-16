from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple

from app.models import Reserva
from app.views import ReservaCreate, ReservaUpdate, ReservaResponse
from app.exceptions import ConflitoHorarioException


class ReservaController:
    """Controller para gerenciar reservas."""
    
    @staticmethod
    def verificar_conflito_horario(
        db: Session,
        sala_id: Optional[int] = None,
        sala: Optional[str] = None,
        data_hora_inicio: datetime = None,
        data_hora_fim: datetime = None,
        reserva_id_excluir: Optional[int] = None
    ) -> bool:
        """
        Verifica se existe conflito de horário para uma sala.
        Retorna True se houver conflito, False caso contrário.
        Pode usar sala_id (preferencial) ou sala (string) para compatibilidade.
        """
        if not sala_id and not sala:
            raise ValueError("É necessário fornecer sala_id ou sala")
        
        # Filtra por sala_id (preferencial) ou sala (string)
        if sala_id:
            query = db.query(Reserva).filter(Reserva.sala_id == sala_id)
        else:
            query = db.query(Reserva).filter(Reserva.sala == sala)
        
        # Adiciona filtros de conflito de horário
        query = query.filter(
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
    def criar(db: Session, reserva: ReservaCreate, responsavel_id: int, sala_id: Optional[int] = None) -> Reserva:
        """Cria uma nova reserva validando conflitos de horário."""
        if reserva.data_hora_fim <= reserva.data_hora_inicio:
            raise ValueError("A data/hora de fim deve ser maior que a data/hora de início")
        
        # Usa sala_id se fornecido, senão usa sala (string) para compatibilidade
        sala_identificador = sala_id if sala_id else reserva.sala
        
        if ReservaController.verificar_conflito_horario(
            db, 
            sala_id=sala_id, 
            sala=reserva.sala if not sala_id else None,
            data_hora_inicio=reserva.data_hora_inicio, 
            data_hora_fim=reserva.data_hora_fim
        ):
            raise ConflitoHorarioException(
                f"Já existe uma reserva para esta sala no horário especificado"
            )
        
        reserva_data = reserva.model_dump()
        if sala_id:
            reserva_data['sala_id'] = sala_id
        
        db_reserva = Reserva(
            **reserva_data,
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
        if "data_hora_inicio" in update_data or "data_hora_fim" in update_data or "sala" in update_data or "sala_id" in update_data:
            nova_sala_id = update_data.get("sala_id", db_reserva.sala_id)
            nova_sala = update_data.get("sala", db_reserva.sala)
            nova_inicio = update_data.get("data_hora_inicio", db_reserva.data_hora_inicio)
            nova_fim = update_data.get("data_hora_fim", db_reserva.data_hora_fim)
            
            if nova_fim <= nova_inicio:
                raise ValueError("A data/hora de fim deve ser maior que a data/hora de início")
            
            if ReservaController.verificar_conflito_horario(
                db, 
                sala_id=nova_sala_id,
                sala=nova_sala if not nova_sala_id else None,
                data_hora_inicio=nova_inicio, 
                data_hora_fim=nova_fim, 
                reserva_id_excluir=reserva_id
            ):
                raise ConflitoHorarioException(
                    f"Já existe uma reserva para esta sala no horário especificado"
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

    @staticmethod
    def listar_por_sala_e_data(
        db: Session, 
        sala_id: int, 
        data: date
    ) -> List[Reserva]:
        """Lista todas as reservas de uma sala em uma data específica."""
        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())
        
        return db.query(Reserva).filter(
            Reserva.sala_id == sala_id,
            Reserva.data_hora_inicio >= inicio_dia,
            Reserva.data_hora_inicio < fim_dia + timedelta(days=1)
        ).order_by(Reserva.data_hora_inicio).all()

    @staticmethod
    def obter_horarios_disponiveis(
        db: Session,
        sala_id: int,
        data: date,
        hora_inicio: str = "08:00:00",
        hora_fim: str = "18:00:00"
    ) -> List[Tuple[datetime, datetime]]:
        """
        Retorna lista de intervalos de horários disponíveis para uma sala em uma data.
        Retorna lista de tuplas (inicio, fim) representando os horários livres.
        """
        # Converte strings de hora para datetime
        hora_inicio_dt = datetime.strptime(hora_inicio, "%H:%M:%S").time()
        hora_fim_dt = datetime.strptime(hora_fim, "%H:%M:%S").time()
        
        inicio_dia = datetime.combine(data, hora_inicio_dt)
        fim_dia = datetime.combine(data, hora_fim_dt)
        
        # Busca todas as reservas do dia
        reservas = db.query(Reserva).filter(
            Reserva.sala_id == sala_id,
            or_(
                and_(
                    Reserva.data_hora_inicio >= inicio_dia,
                    Reserva.data_hora_inicio < fim_dia
                ),
                and_(
                    Reserva.data_hora_fim > inicio_dia,
                    Reserva.data_hora_fim <= fim_dia
                ),
                and_(
                    Reserva.data_hora_inicio <= inicio_dia,
                    Reserva.data_hora_fim >= fim_dia
                )
            )
        ).order_by(Reserva.data_hora_inicio).all()
        
        # Calcula intervalos disponíveis
        horarios_disponiveis = []
        horario_atual = inicio_dia
        
        for reserva in reservas:
            # Se há um intervalo livre antes da reserva
            if horario_atual < reserva.data_hora_inicio:
                horarios_disponiveis.append((horario_atual, reserva.data_hora_inicio))
            
            # Atualiza o horário atual para depois do fim da reserva
            if reserva.data_hora_fim > horario_atual:
                horario_atual = reserva.data_hora_fim
        
        # Se ainda há tempo disponível após a última reserva
        if horario_atual < fim_dia:
            horarios_disponiveis.append((horario_atual, fim_dia))
        
        return horarios_disponiveis

    @staticmethod
    def verificar_disponibilidade(
        db: Session,
        sala_id: int,
        data_hora_inicio: datetime,
        data_hora_fim: datetime
    ) -> bool:
        """
        Verifica se um horário específico está disponível para uma sala.
        Retorna True se disponível, False se ocupado.
        """
        return not ReservaController.verificar_conflito_horario(
            db,
            sala_id=sala_id,
            data_hora_inicio=data_hora_inicio,
            data_hora_fim=data_hora_fim
        )

    @staticmethod
    def obter_horarios_disponiveis_por_hora(
        db: Session,
        sala_id: int,
        data: date,
        hora_inicio: str = "08:00:00",
        hora_fim: str = "18:00:00"
    ) -> List[str]:
        """
        Retorna lista de horários disponíveis em formato de slots de 1 hora.
        Retorna lista de strings no formato "HH:MM" representando as horas disponíveis.
        Cada hora representa um slot de 1 hora disponível (ex: "08:00", "09:00", "10:00").
        """
        # Converte strings de hora para datetime
        hora_inicio_dt = datetime.strptime(hora_inicio, "%H:%M:%S").time()
        hora_fim_dt = datetime.strptime(hora_fim, "%H:%M:%S").time()
        
        inicio_dia = datetime.combine(data, hora_inicio_dt)
        fim_dia = datetime.combine(data, hora_fim_dt)
        
        # Busca todas as reservas do dia que se sobrepõem ao período
        reservas = db.query(Reserva).filter(
            Reserva.sala_id == sala_id,
            or_(
                and_(
                    Reserva.data_hora_inicio >= inicio_dia,
                    Reserva.data_hora_inicio < fim_dia
                ),
                and_(
                    Reserva.data_hora_fim > inicio_dia,
                    Reserva.data_hora_fim <= fim_dia
                ),
                and_(
                    Reserva.data_hora_inicio <= inicio_dia,
                    Reserva.data_hora_fim >= fim_dia
                )
            )
        ).order_by(Reserva.data_hora_inicio).all()
        
        # Cria lista de todas as horas do período
        horas_disponiveis = []
        hora_atual = inicio_dia
        
        while hora_atual < fim_dia:
            hora_fim_slot = hora_atual + timedelta(hours=1)
            
            # Verifica se este slot de 1 hora está livre
            disponivel = True
            for reserva in reservas:
                # Verifica se há sobreposição
                if not (hora_fim_slot <= reserva.data_hora_inicio or hora_atual >= reserva.data_hora_fim):
                    disponivel = False
                    break
            
            if disponivel:
                # Adiciona apenas a hora (formato "HH:MM")
                horas_disponiveis.append(hora_atual.strftime("%H:%M"))
            
            # Avança para a próxima hora
            hora_atual = hora_fim_slot
        
        return horas_disponiveis



