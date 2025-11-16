from sqlalchemy.orm import Session
from typing import Optional, List

from app.models import Sala, Usuario
from app.views import SalaCreate, SalaUpdate
from app.exceptions import ConflitoHorarioException


class SalaController:
    """Controller para gerenciar salas de reunião."""
    
    @staticmethod
    def criar(db: Session, sala: SalaCreate, criador_id: int) -> Sala:
        """Cria uma nova sala de reunião. Apenas admins podem criar salas."""
        # Verifica se o usuário é admin
        usuario = db.query(Usuario).filter(Usuario.id == criador_id).first()
        if not usuario or not usuario.admin:
            raise PermissionError("Apenas administradores podem criar salas")
        
        db_sala = Sala(
            **sala.model_dump(),
            criador_id=criador_id
        )
        db.add(db_sala)
        db.commit()
        db.refresh(db_sala)
        return db_sala

    @staticmethod
    def obter_por_id(db: Session, sala_id: int) -> Optional[Sala]:
        """Obtém uma sala por ID."""
        return db.query(Sala).filter(Sala.id == sala_id).first()

    @staticmethod
    def listar(db: Session, skip: int = 0, limit: int = 100, apenas_ativas: bool = False) -> List[Sala]:
        """Lista todas as salas."""
        query = db.query(Sala)
        if apenas_ativas:
            query = query.filter(Sala.ativa == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def listar_por_criador(db: Session, criador_id: int, skip: int = 0, limit: int = 100) -> List[Sala]:
        """Lista salas criadas por um usuário específico."""
        return db.query(Sala).filter(
            Sala.criador_id == criador_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def atualizar(
        db: Session,
        sala_id: int,
        sala_update: SalaUpdate,
        criador_id: int
    ) -> Optional[Sala]:
        """Atualiza uma sala. Apenas admins podem atualizar salas."""
        db_sala = SalaController.obter_por_id(db, sala_id)
        if not db_sala:
            return None
        
        # Verifica se o usuário é admin
        usuario = db.query(Usuario).filter(Usuario.id == criador_id).first()
        if not usuario or not usuario.admin:
            return None
        
        update_data = sala_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_sala, field, value)
        
        db.commit()
        db.refresh(db_sala)
        return db_sala

    @staticmethod
    def deletar(db: Session, sala_id: int, criador_id: int) -> bool:
        """Deleta uma sala. Apenas admins podem deletar salas."""
        db_sala = SalaController.obter_por_id(db, sala_id)
        if not db_sala:
            return False
        
        # Verifica se o usuário é admin
        usuario = db.query(Usuario).filter(Usuario.id == criador_id).first()
        if not usuario or not usuario.admin:
            return False
        
        db.delete(db_sala)
        db.commit()
        return True

