from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UsuarioBase(BaseModel):
    username: str
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioResponse(UsuarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ReservaBase(BaseModel):
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cafe_quantidade: Optional[int] = Field(None, ge=0)
    cafe_descricao: Optional[str] = None


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    local: Optional[str] = None
    sala: Optional[str] = None
    sala_id: Optional[int] = None
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    cafe_quantidade: Optional[int] = Field(None, ge=0)
    cafe_descricao: Optional[str] = None


class ReservaResponse(ReservaBase):
    id: int
    responsavel_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalaBase(BaseModel):
    nome: str
    local: str
    capacidade: Optional[int] = Field(None, ge=1)
    descricao: Optional[str] = None


class SalaCreate(SalaBase):
    pass


class SalaUpdate(BaseModel):
    nome: Optional[str] = None
    local: Optional[str] = None
    capacidade: Optional[int] = Field(None, ge=1)
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


class SalaResponse(SalaBase):
    id: int
    criador_id: int
    ativa: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
