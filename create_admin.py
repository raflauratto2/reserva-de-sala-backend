"""
Script para criar usuário administrador.

Uso:
    python create_admin.py <username> <email> <password>

Exemplo:
    python create_admin.py admin admin@example.com senha123
"""
import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Usuario
from app.controllers.auth_controller import AuthController


def criar_admin(username: str, email: str, password: str):
    """Cria um usuário administrador."""
    db: Session = SessionLocal()
    try:
        # Verifica se já existe usuário com esse username
        usuario_existente = db.query(Usuario).filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first()
        
        if usuario_existente:
            if usuario_existente.username == username:
                print(f"Erro: Username '{username}' já está em uso.")
                return False
            if usuario_existente.email == email:
                print(f"Erro: Email '{email}' já está em uso.")
                return False
        
        # Cria usuário admin
        admin = AuthController.criar_usuario(db, username, email, password, admin=True)
        print(f"✅ Usuário administrador criado com sucesso!")
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Admin: {admin.admin}")
        return True
        
    except Exception as e:
        print(f"Erro ao criar usuário admin: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python create_admin.py <username> <email> <password>")
        print("Exemplo: python create_admin.py admin admin@example.com senha123")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    criar_admin(username, email, password)

