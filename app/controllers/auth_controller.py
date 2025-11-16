from sqlalchemy.orm import Session
from typing import Optional, List

from app.models import Usuario
from app.auth import get_password_hash


class AuthController:
    """Controller para gerenciar autenticação e usuários."""
    
    @staticmethod
    def criar_usuario(db: Session, username: str, email: str, password: str, nome: Optional[str] = None, admin: bool = False) -> Usuario:
        """Cria um novo usuário."""
        # Valida tamanho da senha antes de fazer hash (bcrypt tem limite de 72 bytes)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError("A senha não pode ter mais de 72 caracteres")
        
        hashed_password = get_password_hash(password)
        db_user = Usuario(
            nome=nome,
            username=username,
            email=email,
            hashed_password=hashed_password,
            admin=admin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def atualizar_usuario(
        db: Session,
        usuario_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Optional[Usuario]:
        """Atualiza os dados de um usuário."""
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
        
        # Atualiza nome se fornecido
        if nome is not None:
            usuario.nome = nome
        
        # Atualiza email se fornecido (verifica se já existe)
        if email is not None:
            # Verifica se o email já está em uso por outro usuário
            existing_user = db.query(Usuario).filter(
                Usuario.email == email,
                Usuario.id != usuario_id
            ).first()
            if existing_user:
                raise ValueError("Email já está em uso")
            usuario.email = email
        
        # Atualiza senha se fornecido
        if password is not None:
            # Valida tamanho da senha
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                raise ValueError("A senha não pode ter mais de 72 caracteres")
            usuario.hashed_password = get_password_hash(password)
        
        db.commit()
        db.refresh(usuario)
        return usuario
    
    @staticmethod
    def listar_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Lista todos os usuários."""
        return db.query(Usuario).offset(skip).limit(limit).all()
    
    @staticmethod
    def obter_usuario_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
        """Obtém um usuário por ID."""
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    @staticmethod
    def deletar_usuario(db: Session, usuario_id: int) -> bool:
        """Deleta um usuário."""
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return False
        
        db.delete(usuario)
        db.commit()
        return True
    
    @staticmethod
    def atualizar_usuario_admin(
        db: Session,
        usuario_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        admin: Optional[bool] = None
    ) -> Optional[Usuario]:
        """
        Atualiza um usuário (para uso por administradores).
        Permite atualizar nome, email, senha e status de admin.
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
        
        if nome is not None:
            usuario.nome = nome
        
        if email is not None:
            # Verifica se o email já está em uso por outro usuário
            existing_user = db.query(Usuario).filter(
                Usuario.email == email,
                Usuario.id != usuario_id
            ).first()
            if existing_user:
                raise ValueError("Email já está em uso")
            usuario.email = email
        
        if password is not None:
            if len(password.encode('utf-8')) > 72:
                raise ValueError("A senha não pode ter mais de 72 caracteres")
            usuario.hashed_password = get_password_hash(password)
        
        if admin is not None:
            usuario.admin = admin
        
        db.commit()
        db.refresh(usuario)
        return usuario



