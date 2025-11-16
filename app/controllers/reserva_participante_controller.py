from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import and_

from app.models import ReservaParticipante, Reserva, Usuario
from app.views import ReservaParticipanteCreate


class ReservaParticipanteController:
    """Controller para gerenciar participantes de reservas."""
    
    @staticmethod
    def adicionar_participante(
        db: Session,
        reserva_id: int,
        usuario_id: int,
        responsavel_id: int
    ) -> Optional[ReservaParticipante]:
        """
        Adiciona um participante a uma reserva.
        Apenas o responsável pela reserva pode adicionar participantes.
        Não permite adicionar admins como participantes.
        """
        # Verifica se a reserva existe e se o usuário é o responsável
        reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            return None
        
        if reserva.responsavel_id != responsavel_id:
            return None
        
        # Verifica se o usuário a ser adicionado existe e não é admin
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario or usuario.admin:
            return None
        
        # Verifica se o participante já foi adicionado
        participante_existente = db.query(ReservaParticipante).filter(
            and_(
                ReservaParticipante.reserva_id == reserva_id,
                ReservaParticipante.usuario_id == usuario_id
            )
        ).first()
        
        if participante_existente:
            return participante_existente
        
        # Cria novo participante
        participante = ReservaParticipante(
            reserva_id=reserva_id,
            usuario_id=usuario_id,
            notificado=False,
            visto=False
        )
        db.add(participante)
        db.commit()
        db.refresh(participante)
        return participante
    
    @staticmethod
    def remover_participante(
        db: Session,
        reserva_id: int,
        usuario_id: int,
        responsavel_id: int
    ) -> bool:
        """
        Remove um participante de uma reserva.
        Apenas o responsável pela reserva pode remover participantes.
        """
        # Verifica se a reserva existe e se o usuário é o responsável
        reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            return False
        
        if reserva.responsavel_id != responsavel_id:
            return False
        
        # Remove o participante
        participante = db.query(ReservaParticipante).filter(
            and_(
                ReservaParticipante.reserva_id == reserva_id,
                ReservaParticipante.usuario_id == usuario_id
            )
        ).first()
        
        if not participante:
            return False
        
        db.delete(participante)
        db.commit()
        return True
    
    @staticmethod
    def listar_participantes(db: Session, reserva_id: int) -> List[ReservaParticipante]:
        """Lista todos os participantes de uma reserva com relacionamento usuario carregado."""
        return db.query(ReservaParticipante).options(
            joinedload(ReservaParticipante.usuario)
        ).filter(
            ReservaParticipante.reserva_id == reserva_id
        ).all()
    
    @staticmethod
    def listar_reservas_do_usuario(
        db: Session,
        usuario_id: int,
        apenas_nao_notificadas: bool = False,
        apenas_nao_vistas: bool = False
    ) -> List[ReservaParticipante]:
        """
        Lista todas as reservas em que o usuário é participante.
        Se apenas_nao_notificadas=True, retorna apenas reservas não notificadas.
        Se apenas_nao_vistas=True, retorna apenas reservas não vistas.
        """
        query = db.query(ReservaParticipante).options(
            joinedload(ReservaParticipante.usuario),
            joinedload(ReservaParticipante.reserva).joinedload(Reserva.responsavel),
            joinedload(ReservaParticipante.reserva).joinedload(Reserva.sala_rel)
        ).filter(
            ReservaParticipante.usuario_id == usuario_id
        )
        
        if apenas_nao_notificadas:
            query = query.filter(ReservaParticipante.notificado == False)
        
        if apenas_nao_vistas:
            query = query.filter(ReservaParticipante.visto == False)
        
        return query.order_by(ReservaParticipante.created_at.desc()).all()
    
    @staticmethod
    def contar_reservas_nao_vistas(db: Session, usuario_id: int) -> int:
        """Conta quantas reservas não vistas o usuário tem."""
        return db.query(ReservaParticipante).filter(
            ReservaParticipante.usuario_id == usuario_id,
            ReservaParticipante.visto == False
        ).count()
    
    @staticmethod
    def marcar_como_notificado(
        db: Session,
        reserva_id: int,
        usuario_id: int
    ) -> bool:
        """Marca uma reserva como notificada para um usuário."""
        participante = db.query(ReservaParticipante).filter(
            and_(
                ReservaParticipante.reserva_id == reserva_id,
                ReservaParticipante.usuario_id == usuario_id
            )
        ).first()
        
        if not participante:
            return False
        
        participante.notificado = True
        db.commit()
        return True
    
    @staticmethod
    def marcar_como_visto(
        db: Session,
        reserva_id: int,
        usuario_id: int
    ) -> bool:
        """Marca uma reserva como vista para um usuário."""
        participante = db.query(ReservaParticipante).filter(
            and_(
                ReservaParticipante.reserva_id == reserva_id,
                ReservaParticipante.usuario_id == usuario_id
            )
        ).first()
        
        if not participante:
            return False
        
        participante.visto = True
        db.commit()
        return True
    
    @staticmethod
    def listar_usuarios_nao_admin(db: Session) -> List[Usuario]:
        """Lista todos os usuários que não são administradores."""
        return db.query(Usuario).filter(Usuario.admin == False).all()

