from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://reservas_user:reservas_pass@localhost:5432/reservas_db"
    secret_key: str = "sua-chave-secreta-aqui-altere-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()

