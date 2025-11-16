from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
import os

from app.graphql.schema import schema

app = FastAPI(
    title="Sistema de Reservas API",
    description="API para gerenciamento de reservas com GraphQL",
    version="1.0.0",
    docs_url=None,  # Desabilita o Swagger UI
    redoc_url=None  # Desabilita o ReDoc
)

# Configuração CORS
# Lista explícita de portas comuns + regex como fallback para desenvolvimento
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Lista completa de portas comuns para desenvolvimento
common_ports = [
    3000, 3001, 3002, 3003,  # React/Vite padrão e alternativas
    5173, 5174, 5175, 5176,  # Vite portas alternativas
    8080, 8081, 8082,        # Vue CLI e outras
    4200, 4201,              # Angular
    5000, 5001,              # Outros frameworks
    8001, 8002,              # Portas alternativas
]

# Gera lista de origens permitidas
allowed_origins = []
for port in common_ports:
    allowed_origins.extend([
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
    ])

# Aplica configuração CORS
if ENVIRONMENT == "development":
    # Em desenvolvimento: lista explícita + regex como fallback
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):[0-9]+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    print(f"[CORS] Modo: DESENVOLVIMENTO - {len(allowed_origins)} origens explícitas + regex fallback")
else:
    # Em produção: apenas lista explícita (sem regex)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    print(f"[CORS] Modo: PRODUÇÃO - {len(allowed_origins)} origens explícitas")

# Rota GraphQL com GraphiQL
graphql_app = GraphQLRouter(schema, graphiql=True)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def root():
    return {
        "message": "Sistema de Reservas API - GraphQL",
        "graphql": "/graphql",
        "status": "online"
    }


@app.get("/health")
def health_check():
    """Endpoint de verificação de saúde da API"""
    return {
        "status": "healthy",
        "service": "Sistema de Reservas API",
        "version": "1.0.0"
    }

