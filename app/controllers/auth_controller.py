from sqlalchemy.orm import Session
from typing import Optional

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



