from typing import List, Optional
from datetime import datetime
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Reserva, Usuario
from app.views import ReservaCreate, ReservaUpdate
from app.controllers.reserva_controller import ReservaController
from app.controllers.auth_controller import AuthController
from app.auth import authenticate_user, create_access_token
from app.config import settings
from app.exceptions import ConflitoHorarioException
from datetime import timedelta


@strawberry.type
class UsuarioType:
    id: int
    username: str
    email: str
    created_at: datetime


@strawberry.type
class ReservaType:
    id: int
    local: str
    sala: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    responsavel_id: int
    cafe_quantidade: Optional[int]
    cafe_descricao: Optional[str]
    created_at: datetime
    updated_at: datetime


@strawberry.input
class ReservaInput:
    local: str
    sala: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None


@strawberry.input
class ReservaUpdateInput:
    local: Optional[str] = None
    sala: Optional[str] = None
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None


@strawberry.input
class UsuarioInput:
    username: str
    email: str
    password: str


@strawberry.input
class LoginInput:
    username: str
    password: str


@strawberry.type
class TokenType:
    access_token: str
    token_type: str


def get_current_user_from_context(info) -> Usuario:
    """Obtém o usuário atual do contexto GraphQL."""
    request = info.context["request"]
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise Exception("Token de autenticação não fornecido")
    
    token = auth_header.replace("Bearer ", "")
    
    from app.database import SessionLocal
    from app.auth import get_user_by_username
    from jose import jwt
    from app.config import settings
    
    db = SessionLocal()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        if not username:
            raise Exception("Token inválido")
        
        user = get_user_by_username(db, username)
        if not user:
            raise Exception("Usuário não encontrado")
        return user
    except jwt.JWTError:
        raise Exception("Token inválido ou expirado")
    finally:
        db.close()


@strawberry.type
class Query:
    @strawberry.field
    def reservas(
        self,
        info,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReservaType]:
        """Lista todas as reservas."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            reservas = ReservaController.listar(db, skip=skip, limit=limit)
            return [
                ReservaType(
                    id=r.id,
                    local=r.local,
                    sala=r.sala,
                    data_hora_inicio=r.data_hora_inicio,
                    data_hora_fim=r.data_hora_fim,
                    responsavel_id=r.responsavel_id,
                    cafe_quantidade=r.cafe_quantidade,
                    cafe_descricao=r.cafe_descricao,
                    created_at=r.created_at,
                    updated_at=r.updated_at
                )
                for r in reservas
            ]
        finally:
            db.close()
    
    @strawberry.field
    def reserva(self, info, reserva_id: int) -> Optional[ReservaType]:
        """Obtém uma reserva específica por ID."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            r = ReservaController.obter_por_id(db, reserva_id)
            if not r:
                return None
            return ReservaType(
                id=r.id,
                local=r.local,
                sala=r.sala,
                data_hora_inicio=r.data_hora_inicio,
                data_hora_fim=r.data_hora_fim,
                responsavel_id=r.responsavel_id,
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
        finally:
            db.close()


@strawberry.type
class Mutation:
    @strawberry.mutation
    def criar_usuario(self, usuario: UsuarioInput) -> UsuarioType:
        """Cria um novo usuário."""
        db = SessionLocal()
        try:
            # Valida tamanho da senha (bcrypt tem limite de 72 bytes)
            if len(usuario.password.encode('utf-8')) > 72:
                raise Exception("A senha não pode ter mais de 72 caracteres")
            
            # Verifica se username já existe
            existing_user = db.query(Usuario).filter(Usuario.username == usuario.username).first()
            if existing_user:
                raise Exception("Username já está em uso")
            
            # Verifica se email já existe
            existing_email = db.query(Usuario).filter(Usuario.email == usuario.email).first()
            if existing_email:
                raise Exception("Email já está em uso")
            
            novo_usuario = AuthController.criar_usuario(
                db, usuario.username, usuario.email, usuario.password
            )
            return UsuarioType(
                id=novo_usuario.id,
                username=novo_usuario.username,
                email=novo_usuario.email,
                created_at=novo_usuario.created_at
            )
        finally:
            db.close()
    
    @strawberry.mutation
    def login(self, login_data: LoginInput) -> TokenType:
        """Faz login e retorna um token de acesso."""
        db = SessionLocal()
        try:
            # Valida tamanho da senha (bcrypt tem limite de 72 bytes)
            if len(login_data.password.encode('utf-8')) > 72:
                raise Exception("A senha não pode ter mais de 72 caracteres")
            
            user = authenticate_user(db, login_data.username, login_data.password)
            if not user:
                raise Exception("Username ou senha incorretos")
            
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            return TokenType(
                access_token=access_token,
                token_type="bearer"
            )
        finally:
            db.close()
    
    @strawberry.mutation
    def criar_reserva(self, info, reserva: ReservaInput) -> ReservaType:
        """Cria uma nova reserva."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            reserva_create = ReservaCreate(
                local=reserva.local,
                sala=reserva.sala,
                data_hora_inicio=reserva.data_hora_inicio,
                data_hora_fim=reserva.data_hora_fim,
                cafe_quantidade=reserva.cafe_quantidade,
                cafe_descricao=reserva.cafe_descricao
            )
            r = ReservaController.criar(db, reserva_create, current_user.id)
            return ReservaType(
                id=r.id,
                local=r.local,
                sala=r.sala,
                data_hora_inicio=r.data_hora_inicio,
                data_hora_fim=r.data_hora_fim,
                responsavel_id=r.responsavel_id,
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
        except ConflitoHorarioException as e:
            raise Exception(str(e))
        except ValueError as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def atualizar_reserva(
        self,
        info,
        reserva_id: int,
        reserva: ReservaUpdateInput
    ) -> Optional[ReservaType]:
        """Atualiza uma reserva existente."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            reserva_update = ReservaUpdate(
                local=reserva.local,
                sala=reserva.sala,
                data_hora_inicio=reserva.data_hora_inicio,
                data_hora_fim=reserva.data_hora_fim,
                cafe_quantidade=reserva.cafe_quantidade,
                cafe_descricao=reserva.cafe_descricao
            )
            r = ReservaController.atualizar(db, reserva_id, reserva_update, current_user.id)
            if not r:
                return None
            return ReservaType(
                id=r.id,
                local=r.local,
                sala=r.sala,
                data_hora_inicio=r.data_hora_inicio,
                data_hora_fim=r.data_hora_fim,
                responsavel_id=r.responsavel_id,
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
        except ConflitoHorarioException as e:
            raise Exception(str(e))
        except ValueError as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def deletar_reserva(self, info, reserva_id: int) -> bool:
        """Deleta uma reserva."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            return ReservaController.deletar(db, reserva_id, current_user.id)
        finally:
            db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)

