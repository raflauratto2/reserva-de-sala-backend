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
    local: str
    sala: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cafe_quantidade: Optional[int] = Field(None, ge=0)
    cafe_descricao: Optional[str] = None


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    local: Optional[str] = None
    sala: Optional[str] = None
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

