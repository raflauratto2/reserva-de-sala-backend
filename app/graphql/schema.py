from typing import List, Optional
from datetime import datetime
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Reserva, Usuario, Sala, ReservaParticipante
from app.views import ReservaCreate, ReservaUpdate, SalaCreate, SalaUpdate
from app.controllers.reserva_controller import ReservaController
from app.controllers.sala_controller import SalaController
from app.controllers.auth_controller import AuthController
from app.controllers.reserva_participante_controller import ReservaParticipanteController
from app.auth import authenticate_user, create_access_token
from app.config import settings
from app.exceptions import ConflitoHorarioException
from datetime import timedelta


def criar_responsavel_type(usuario):
    """Helper para criar ResponsavelType a partir de um Usuario."""
    if not usuario:
        return None
    return ResponsavelType(
        id=usuario.id,
        nome=usuario.nome,
        username=usuario.username,
        email=usuario.email
    )


def criar_reserva_type_completa(reserva):
    """Helper para criar ReservaType completo a partir de uma Reserva."""
    if not reserva:
        return None
    
    # Carrega a sala se existir
    sala_type = None
    if reserva.sala_rel:
        sala_type = SalaType(
            id=reserva.sala_rel.id,
            nome=reserva.sala_rel.nome,
            local=reserva.sala_rel.local,
            capacidade=reserva.sala_rel.capacidade,
            descricao=reserva.sala_rel.descricao,
            criador_id=reserva.sala_rel.criador_id,
            ativa=reserva.sala_rel.ativa,
            created_at=reserva.sala_rel.created_at,
            updated_at=reserva.sala_rel.updated_at
        )
    
    return ReservaType(
        id=reserva.id,
        local=reserva.local,
        sala=reserva.sala,
        sala_id=reserva.sala_id,
        data_hora_inicio=reserva.data_hora_inicio,
        data_hora_fim=reserva.data_hora_fim,
        responsavel_id=reserva.responsavel_id,
        responsavel=criar_responsavel_type(reserva.responsavel) if reserva.responsavel else None,
        cafe_quantidade=reserva.cafe_quantidade,
        cafe_descricao=reserva.cafe_descricao,
        link_meet=reserva.link_meet,
        created_at=reserva.created_at,
        updated_at=reserva.updated_at,
        sala_rel=sala_type
    )


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
class ResponsavelType:
    id: int
    nome: Optional[str]
    username: str
    email: str


@strawberry.type
class ReservaParticipanteType:
    id: int
    reserva_id: int
    usuario_id: int
    notificado: bool
    visto: bool  # Se o usuário já viu a notificação
    created_at: datetime
    usuario: Optional[ResponsavelType] = None
    reserva: Optional["ReservaType"] = None  # Dados da reserva


@strawberry.type
class ReservaType:
    id: int
    local: Optional[str]
    sala: Optional[str]
    sala_id: Optional[int]
    data_hora_inicio: datetime
    data_hora_fim: datetime
    responsavel_id: int
    responsavel: Optional[ResponsavelType] = None
    cafe_quantidade: Optional[int]
    cafe_descricao: Optional[str]
    link_meet: Optional[str]  # Link da sala de meet (URL)
    sala_rel: Optional["SalaType"] = None  # Dados completos da sala
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ReservaHistoricoType:
    """Tipo para histórico de reservas do usuário."""
    reserva: ReservaType
    sou_responsavel: bool  # True se o usuário é o responsável, False se é apenas participante


@strawberry.input
class ReservaInput:
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None
    link_meet: Optional[str] = None  # Link da sala de meet (URL)


@strawberry.input
class ReservaUpdateInput:
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    cafe_quantidade: Optional[int] = None
    cafe_descricao: Optional[str] = None
    link_meet: Optional[str] = None  # Link da sala de meet (URL)


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


@strawberry.input
class UsuarioUpdateInput:
    nome: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


@strawberry.input
class UsuarioAdminInput:
    nome: Optional[str] = None
    username: str
    email: str
    password: str
    admin: bool = False


@strawberry.input
class UsuarioAdminUpdateInput:
    nome: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    admin: Optional[bool] = None


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
                    responsavel=criar_responsavel_type(r.responsavel),
                    cafe_quantidade=r.cafe_quantidade,
                    cafe_descricao=r.cafe_descricao,
                    link_meet=r.link_meet,
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
                responsavel=criar_responsavel_type(r.responsavel),
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                link_meet=r.link_meet,
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
    def usuarios(self, info, skip: int = 0, limit: int = 100) -> List[UsuarioType]:
        """
        Lista todos os usuários do sistema.
        Apenas administradores podem acessar esta query.
        """
        current_user = get_current_user_from_context(info)
        if not current_user.admin:
            raise Exception("Apenas administradores podem listar usuários")
        
        db = SessionLocal()
        try:
            usuarios = AuthController.listar_usuarios(db, skip=skip, limit=limit)
            return [
                UsuarioType(
                    id=u.id,
                    nome=u.nome,
                    username=u.username,
                    email=u.email,
                    admin=u.admin,
                    created_at=u.created_at
                )
                for u in usuarios
            ]
        finally:
            db.close()
    
    @strawberry.field
    def usuario(self, info, usuario_id: int) -> Optional[UsuarioType]:
        """
        Obtém um usuário específico por ID.
        Apenas administradores podem acessar esta query.
        """
        current_user = get_current_user_from_context(info)
        if not current_user.admin:
            raise Exception("Apenas administradores podem visualizar usuários")
        
        db = SessionLocal()
        try:
            u = AuthController.obter_usuario_por_id(db, usuario_id)
            if not u:
                return None
            return UsuarioType(
                id=u.id,
                nome=u.nome,
                username=u.username,
                email=u.email,
                admin=u.admin,
                created_at=u.created_at
            )
        finally:
            db.close()
    
    @strawberry.field
    def usuarios_nao_admin(
        self,
        info,
        skip: int = 0,
        limit: int = 100
    ) -> List[ResponsavelType]:
        """Lista todos os usuários que não são administradores (para seleção de participantes)."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            usuarios = ReservaParticipanteController.listar_usuarios_nao_admin(db, skip=skip, limit=limit)
            return [
                ResponsavelType(
                    id=u.id,
                    nome=u.nome,
                    username=u.username,
                    email=u.email
                )
                for u in usuarios
            ]
        finally:
            db.close()
    
    @strawberry.field
    def participantes_reserva(self, info, reserva_id: int) -> List[ReservaParticipanteType]:
        """Lista todos os participantes de uma reserva."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            participantes = ReservaParticipanteController.listar_participantes(db, reserva_id)
            return [
                ReservaParticipanteType(
                    id=p.id,
                    reserva_id=p.reserva_id,
                    usuario_id=p.usuario_id,
                    notificado=p.notificado,
                    visto=p.visto,
                    created_at=p.created_at,
                    usuario=criar_responsavel_type(p.usuario) if p.usuario else None,
                    reserva=criar_reserva_type_completa(p.reserva) if p.reserva else None
                )
                for p in participantes
            ]
        finally:
            db.close()
    
    @strawberry.field
    def minhas_reservas_convidadas(
        self,
        info,
        apenas_nao_notificadas: bool = False,
        apenas_nao_vistas: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReservaParticipanteType]:
        """
        Lista todas as reservas em que o usuário atual foi convidado como participante.
        Se apenas_nao_notificadas=True, retorna apenas reservas não notificadas.
        Se apenas_nao_vistas=True, retorna apenas reservas não vistas (útil para notificações).
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            participantes = ReservaParticipanteController.listar_reservas_do_usuario(
                db, current_user.id, apenas_nao_notificadas, apenas_nao_vistas, skip=skip, limit=limit
            )
            return [
                ReservaParticipanteType(
                    id=p.id,
                    reserva_id=p.reserva_id,
                    usuario_id=p.usuario_id,
                    notificado=p.notificado,
                    visto=p.visto,
                    created_at=p.created_at,
                    usuario=criar_responsavel_type(p.usuario) if p.usuario else None,
                    reserva=criar_reserva_type_completa(p.reserva) if p.reserva else None
                )
                for p in participantes
            ]
        finally:
            db.close()
    
    @strawberry.field
    def contar_reservas_nao_vistas(self, info) -> int:
        """
        Conta quantas reservas não vistas o usuário atual tem.
        Útil para exibir o número de notificações no sino.
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            return ReservaParticipanteController.contar_reservas_nao_vistas(db, current_user.id)
        finally:
            db.close()
    
    @strawberry.field
    def meu_historico(
        self,
        info,
        apenas_futuras: bool = False,
        apenas_passadas: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReservaHistoricoType]:
        """
        Lista todas as reuniões (reservas) nas quais o usuário participou ou vai participar.
        Inclui reservas onde o usuário é responsável e onde é participante.
        
        Parâmetros:
        - apenas_futuras: Se True, retorna apenas reservas futuras
        - apenas_passadas: Se True, retorna apenas reservas passadas
        - skip: Número de registros para pular (paginação)
        - limit: Número máximo de registros a retornar
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            historico = ReservaController.listar_historico_usuario(
                db, current_user.id, apenas_futuras, apenas_passadas, skip, limit
            )
            
            resultado = []
            for reserva, is_responsavel in historico:
                sala_type = None
                if reserva.sala_rel:
                    sala_type = SalaType(
                        id=reserva.sala_rel.id,
                        nome=reserva.sala_rel.nome,
                        local=reserva.sala_rel.local,
                        capacidade=reserva.sala_rel.capacidade,
                        descricao=reserva.sala_rel.descricao,
                        criador_id=reserva.sala_rel.criador_id,
                        ativa=reserva.sala_rel.ativa,
                        created_at=reserva.sala_rel.created_at,
                        updated_at=reserva.sala_rel.updated_at
                    )
                
                reserva_type = ReservaType(
                    id=reserva.id,
                    local=reserva.local,
                    sala=reserva.sala,
                    sala_id=reserva.sala_id,
                    data_hora_inicio=reserva.data_hora_inicio,
                    data_hora_fim=reserva.data_hora_fim,
                    responsavel_id=reserva.responsavel_id,
                    responsavel=criar_responsavel_type(reserva.responsavel),
                    cafe_quantidade=reserva.cafe_quantidade,
                    cafe_descricao=reserva.cafe_descricao,
                    link_meet=reserva.link_meet,
                    sala_rel=sala_type,
                    created_at=reserva.created_at,
                    updated_at=reserva.updated_at
                )
                
                resultado.append(ReservaHistoricoType(
                    reserva=reserva_type,
                    sou_responsavel=is_responsavel
                ))
            
            return resultado
        finally:
            db.close()
    
    @strawberry.field
    def reservas_por_sala(
        self,
        info,
        sala_id: int,
        data: str,  # Formato: "YYYY-MM-DD"
        skip: int = 0,
        limit: int = 100
    ) -> List[ReservaType]:
        """Lista todas as reservas de uma sala em uma data específica."""
        get_current_user_from_context(info)  # Valida autenticação
        
        db = SessionLocal()
        try:
            from datetime import date as date_type
            data_obj = datetime.strptime(data, "%Y-%m-%d").date()
            reservas = ReservaController.listar_por_sala_e_data(db, sala_id, data_obj, skip=skip, limit=limit)
            return [
                ReservaType(
                    id=r.id,
                    local=r.local,
                    sala=r.sala,
                    sala_id=r.sala_id,
                    data_hora_inicio=r.data_hora_inicio,
                    data_hora_fim=r.data_hora_fim,
                    responsavel_id=r.responsavel_id,
                    responsavel=criar_responsavel_type(r.responsavel),
                    cafe_quantidade=r.cafe_quantidade,
                    cafe_descricao=r.cafe_descricao,
                    link_meet=r.link_meet,
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
                cafe_descricao=reserva.cafe_descricao,
                link_meet=reserva.link_meet
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
                responsavel=criar_responsavel_type(r.responsavel),
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                link_meet=r.link_meet,
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
                cafe_descricao=reserva.cafe_descricao,
                link_meet=reserva.link_meet
            )
            r = ReservaController.atualizar(db, reserva_id, reserva_update, current_user.id)
            if not r:
                return None
            # Recarrega a reserva com o relacionamento responsavel
            r = ReservaController.obter_por_id(db, r.id)
            return ReservaType(
                id=r.id,
                local=r.local,
                sala=r.sala,
                sala_id=r.sala_id,
                data_hora_inicio=r.data_hora_inicio,
                data_hora_fim=r.data_hora_fim,
                responsavel_id=r.responsavel_id,
                responsavel=criar_responsavel_type(r.responsavel),
                cafe_quantidade=r.cafe_quantidade,
                cafe_descricao=r.cafe_descricao,
                link_meet=r.link_meet,
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
    
    @strawberry.mutation
    def atualizar_perfil(self, info, usuario: UsuarioUpdateInput) -> UsuarioType:
        """Atualiza o perfil do usuário atual."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            usuario_atualizado = AuthController.atualizar_usuario(
                db,
                current_user.id,
                nome=usuario.nome,
                email=usuario.email,
                password=usuario.password
            )
            if not usuario_atualizado:
                raise Exception("Erro ao atualizar perfil")
            
            return UsuarioType(
                id=usuario_atualizado.id,
                nome=usuario_atualizado.nome,
                username=usuario_atualizado.username,
                email=usuario_atualizado.email,
                admin=usuario_atualizado.admin,
                created_at=usuario_atualizado.created_at
            )
        except ValueError as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def adicionar_participante(
        self,
        info,
        reserva_id: int,
        usuario_id: int
    ) -> ReservaParticipanteType:
        """
        Adiciona um participante a uma reserva.
        Apenas o responsável pela reserva pode adicionar participantes.
        Não permite adicionar admins como participantes.
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            participante = ReservaParticipanteController.adicionar_participante(
                db, reserva_id, usuario_id, current_user.id
            )
            if not participante:
                raise Exception("Não foi possível adicionar o participante. Verifique se você é o responsável pela reserva e se o usuário não é admin.")
            
            return ReservaParticipanteType(
                id=participante.id,
                reserva_id=participante.reserva_id,
                usuario_id=participante.usuario_id,
                notificado=participante.notificado,
                visto=participante.visto,
                created_at=participante.created_at,
                usuario=criar_responsavel_type(participante.usuario) if participante.usuario else None,
                reserva=criar_reserva_type_completa(participante.reserva) if participante.reserva else None
            )
        except Exception as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def remover_participante(
        self,
        info,
        reserva_id: int,
        usuario_id: int
    ) -> bool:
        """
        Remove um participante de uma reserva.
        Apenas o responsável pela reserva pode remover participantes.
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            resultado = ReservaParticipanteController.remover_participante(
                db, reserva_id, usuario_id, current_user.id
            )
            if not resultado:
                raise Exception("Não foi possível remover o participante. Verifique se você é o responsável pela reserva.")
            return resultado
        except Exception as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def marcar_reserva_como_notificada(
        self,
        info,
        reserva_id: int
    ) -> bool:
        """Marca uma reserva como notificada para o usuário atual."""
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            resultado = ReservaParticipanteController.marcar_como_notificado(
                db, reserva_id, current_user.id
            )
            if not resultado:
                raise Exception("Reserva não encontrada ou você não é participante desta reserva.")
            return resultado
        except Exception as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def marcar_reserva_como_vista(
        self,
        info,
        reserva_id: int
    ) -> bool:
        """
        Marca uma reserva como vista para o usuário atual.
        Use quando o usuário visualizar a notificação no sino.
        """
        current_user = get_current_user_from_context(info)
        
        db = SessionLocal()
        try:
            resultado = ReservaParticipanteController.marcar_como_visto(
                db, reserva_id, current_user.id
            )
            if not resultado:
                raise Exception("Reserva não encontrada ou você não é participante desta reserva.")
            return resultado
        except Exception as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def criar_usuario_admin(self, info, usuario: UsuarioAdminInput) -> UsuarioType:
        """
        Cria um novo usuário (apenas para administradores).
        Permite definir se o usuário será admin ou não.
        """
        current_user = get_current_user_from_context(info)
        if not current_user.admin:
            raise Exception("Apenas administradores podem criar usuários")
        
        db = SessionLocal()
        try:
            # Valida tamanho da senha
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
                db, usuario.username, usuario.email, usuario.password, 
                nome=usuario.nome, admin=usuario.admin
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
    def atualizar_usuario_admin(
        self,
        info,
        usuario_id: int,
        usuario: UsuarioAdminUpdateInput
    ) -> UsuarioType:
        """
        Atualiza um usuário (apenas para administradores).
        Permite atualizar nome, email, senha e status de admin.
        """
        current_user = get_current_user_from_context(info)
        if not current_user.admin:
            raise Exception("Apenas administradores podem atualizar usuários")
        
        db = SessionLocal()
        try:
            usuario_atualizado = AuthController.atualizar_usuario_admin(
                db,
                usuario_id,
                nome=usuario.nome,
                email=usuario.email,
                password=usuario.password,
                admin=usuario.admin
            )
            if not usuario_atualizado:
                raise Exception("Usuário não encontrado")
            
            return UsuarioType(
                id=usuario_atualizado.id,
                nome=usuario_atualizado.nome,
                username=usuario_atualizado.username,
                email=usuario_atualizado.email,
                admin=usuario_atualizado.admin,
                created_at=usuario_atualizado.created_at
            )
        except ValueError as e:
            raise Exception(str(e))
        finally:
            db.close()
    
    @strawberry.mutation
    def deletar_usuario(self, info, usuario_id: int) -> bool:
        """
        Deleta um usuário (apenas para administradores).
        """
        current_user = get_current_user_from_context(info)
        if not current_user.admin:
            raise Exception("Apenas administradores podem deletar usuários")
        
        db = SessionLocal()
        try:
            resultado = AuthController.deletar_usuario(db, usuario_id)
            if not resultado:
                raise Exception("Usuário não encontrado")
            return resultado
        except Exception as e:
            raise Exception(str(e))
        finally:
            db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)

