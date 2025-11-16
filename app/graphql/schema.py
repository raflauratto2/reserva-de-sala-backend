from typing import List, Optional
from datetime import datetime
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Reserva, Usuario, Sala
from app.views import ReservaCreate, ReservaUpdate, SalaCreate, SalaUpdate
from app.controllers.reserva_controller import ReservaController
from app.controllers.sala_controller import SalaController
from app.controllers.auth_controller import AuthController
from app.auth import authenticate_user, create_access_token
from app.config import settings
from app.exceptions import ConflitoHorarioException
from datetime import timedelta


@strawberry.type
class UsuarioType:
    id: int
    nome: Optional[str]
    username: str
    email: str
    admin: bool
    created_at: datetime


@strawberry.type
class SalaType:
    id: int
    nome: str
    local: str
    capacidade: Optional[int]
    descricao: Optional[str]
    criador_id: int
    ativa: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class HorarioDisponivelType:
    inicio: datetime
    fim: datetime


@strawberry.type
class ReservaType:
    id: int
    local: Optional[str]
    sala: Optional[str]
    sala_id: Optional[int]
    data_hora_inicio: datetime
    data_hora_fim: datetime
    responsavel_id: int
    cafe_quantidade: Optional[int]
    cafe_descricao: Optional[str]
    created_at: datetime
    updated_at: datetime


@strawberry.input
class ReservaInput:
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None


@strawberry.input
class ReservaUpdateInput:
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None


@strawberry.input
class SalaInput:
    nome: str
    local: str
    capacidade: Optional[int] = None
    descricao: Optional[str] = None


@strawberry.input
class SalaUpdateInput:
    nome: Optional[str] = None
    local: Optional[str] = None
    capacidade: Optional[int] = None
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


@strawberry.input
class UsuarioInput:
    nome: Optional[str] = None
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
                    sala_id=r.sala_id,
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
                sala_id=r.sala_id,
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
    
    @strawberry.field
    def salas(
        self,
        info,
        skip: int = 0,
        limit: int = 100,
        apenas_ativas: bool = False
    ) -> List[SalaType]:
        """Lista todas as salas."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            salas = SalaController.listar(db, skip=skip, limit=limit, apenas_ativas=apenas_ativas)
            return [
                SalaType(
                    id=s.id,
                    nome=s.nome,
                    local=s.local,
                    capacidade=s.capacidade,
                    descricao=s.descricao,
                    criador_id=s.criador_id,
                    ativa=s.ativa,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
                for s in salas
            ]
        finally:
            db.close()
    
    @strawberry.field
    def sala(self, info, sala_id: int) -> Optional[SalaType]:
        """Obtém uma sala específica por ID."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            s = SalaController.obter_por_id(db, sala_id)
            if not s:
                return None
            return SalaType(
                id=s.id,
                nome=s.nome,
                local=s.local,
                capacidade=s.capacidade,
                descricao=s.descricao,
                criador_id=s.criador_id,
                ativa=s.ativa,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
        finally:
            db.close()
    
    @strawberry.field
    def minhas_salas(
        self,
        info,
        skip: int = 0,
        limit: int = 100
    ) -> List[SalaType]:
        """Lista as salas criadas pelo usuário atual."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            salas = SalaController.listar_por_criador(db, current_user.id, skip=skip, limit=limit)
            return [
                SalaType(
                    id=s.id,
                    nome=s.nome,
                    local=s.local,
                    capacidade=s.capacidade,
                    descricao=s.descricao,
                    criador_id=s.criador_id,
                    ativa=s.ativa,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
                for s in salas
            ]
        finally:
            db.close()
    
    @strawberry.field
    def meu_perfil(self, info) -> UsuarioType:
        """Retorna o perfil do usuário atual, incluindo se é admin."""
        current_user = get_current_user_from_context(info)
        
        return UsuarioType(
            id=current_user.id,
            nome=current_user.nome,
            username=current_user.username,
            email=current_user.email,
            admin=current_user.admin,
            created_at=current_user.created_at
        )
    
    @strawberry.field
    def reservas_por_sala(
        self,
        info,
        sala_id: int,
        data: str  # Formato: "YYYY-MM-DD"
    ) -> List[ReservaType]:
        """Lista todas as reservas de uma sala em uma data específica."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            from datetime import date as date_type
            data_obj = datetime.strptime(data, "%Y-%m-%d").date()
            reservas = ReservaController.listar_por_sala_e_data(db, sala_id, data_obj)
            return [
                ReservaType(
                    id=r.id,
                    local=r.local,
                    sala=r.sala,
                    sala_id=r.sala_id,
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
    def horarios_disponiveis(
        self,
        info,
        sala_id: int,
        data: str,  # Formato: "YYYY-MM-DD"
        hora_inicio: Optional[str] = "08:00:00",  # Formato: "HH:MM:SS"
        hora_fim: Optional[str] = "18:00:00"  # Formato: "HH:MM:SS"
    ) -> List[HorarioDisponivelType]:
        """Retorna os horários disponíveis de uma sala em uma data específica."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            from datetime import date as date_type
            data_obj = datetime.strptime(data, "%Y-%m-%d").date()
            horarios = ReservaController.obter_horarios_disponiveis(
                db, sala_id, data_obj, hora_inicio, hora_fim
            )
            return [
                HorarioDisponivelType(inicio=inicio, fim=fim)
                for inicio, fim in horarios
            ]
        finally:
            db.close()
    
    @strawberry.field
    def verificar_disponibilidade(
        self,
        info,
        sala_id: int,
        data_hora_inicio: str,  # Formato ISO 8601: "YYYY-MM-DDTHH:mm:ss"
        data_hora_fim: str  # Formato ISO 8601: "YYYY-MM-DDTHH:mm:ss"
    ) -> bool:
        """Verifica se um horário específico está disponível para uma sala."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            # Parse ISO 8601 format
            inicio = datetime.strptime(data_hora_inicio, "%Y-%m-%dT%H:%M:%S")
            fim = datetime.strptime(data_hora_fim, "%Y-%m-%dT%H:%M:%S")
            return ReservaController.verificar_disponibilidade(db, sala_id, inicio, fim)
        except ValueError:
            # Tenta formato com timezone
            try:
                inicio = datetime.fromisoformat(data_hora_inicio.replace('Z', '+00:00'))
                fim = datetime.fromisoformat(data_hora_fim.replace('Z', '+00:00'))
                return ReservaController.verificar_disponibilidade(db, sala_id, inicio, fim)
            except:
                raise Exception("Formato de data/hora inválido. Use: YYYY-MM-DDTHH:mm:ss")
        finally:
            db.close()
    
    @strawberry.field
    def horarios_disponiveis_por_hora(
        self,
        info,
        sala_id: int,
        data: str,  # Formato: "YYYY-MM-DD"
        hora_inicio: Optional[str] = "08:00:00",  # Formato: "HH:MM:SS"
        hora_fim: Optional[str] = "18:00:00"  # Formato: "HH:MM:SS"
    ) -> List[str]:
        """
        Retorna lista de horários disponíveis em slots de 1 hora.
        Retorna lista de strings no formato "HH:MM" (ex: ["08:00", "09:00", "10:00"]).
        Cada hora representa um slot de 1 hora disponível para reserva.
        """
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            from datetime import date as date_type
            data_obj = datetime.strptime(data, "%Y-%m-%d").date()
            horas = ReservaController.obter_horarios_disponiveis_por_hora(
                db, sala_id, data_obj, hora_inicio, hora_fim
            )
            return horas
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
                db, usuario.username, usuario.email, usuario.password, nome=usuario.nome
            )
            return UsuarioType(
                id=novo_usuario.id,
                nome=novo_usuario.nome,
                username=novo_usuario.username,
                email=novo_usuario.email,
                admin=novo_usuario.admin,
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
                sala_id=reserva.sala_id,
                data_hora_inicio=reserva.data_hora_inicio,
                data_hora_fim=reserva.data_hora_fim,
                cafe_quantidade=reserva.cafe_quantidade,
                cafe_descricao=reserva.cafe_descricao
            )
            r = ReservaController.criar(db, reserva_create, current_user.id, sala_id=reserva.sala_id)
            return ReservaType(
                id=r.id,
                local=r.local,
                sala=r.sala,
                sala_id=r.sala_id,
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
                sala_id=reserva.sala_id,
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
                sala_id=r.sala_id,
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
    
    @strawberry.mutation
    def criar_sala(self, info, sala: SalaInput) -> SalaType:
        """Cria uma nova sala de reunião. Apenas administradores podem criar salas."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            sala_create = SalaCreate(
                nome=sala.nome,
                local=sala.local,
                capacidade=sala.capacidade,
                descricao=sala.descricao
            )
            s = SalaController.criar(db, sala_create, current_user.id)
            return SalaType(
                id=s.id,
                nome=s.nome,
                local=s.local,
                capacidade=s.capacidade,
                descricao=s.descricao,
                criador_id=s.criador_id,
                ativa=s.ativa,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
        except PermissionError as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def atualizar_sala(
        self,
        info,
        sala_id: int,
        sala: SalaUpdateInput
    ) -> Optional[SalaType]:
        """Atualiza uma sala existente. Apenas administradores podem atualizar salas."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            sala_update = SalaUpdate(
                nome=sala.nome,
                local=sala.local,
                capacidade=sala.capacidade,
                descricao=sala.descricao,
                ativa=sala.ativa
            )
            s = SalaController.atualizar(db, sala_id, sala_update, current_user.id)
            if not s:
                raise Exception("Sala não encontrada ou você não tem permissão para atualizá-la")
            return SalaType(
                id=s.id,
                nome=s.nome,
                local=s.local,
                capacidade=s.capacidade,
                descricao=s.descricao,
                criador_id=s.criador_id,
                ativa=s.ativa,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
        finally:
            db.close()
    
    @strawberry.mutation
    def deletar_sala(self, info, sala_id: int) -> bool:
        """Deleta uma sala. Apenas administradores podem deletar salas."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            resultado = SalaController.deletar(db, sala_id, current_user.id)
            if not resultado:
                raise Exception("Sala não encontrada ou você não tem permissão para deletá-la")
            return resultado
        finally:
            db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)

