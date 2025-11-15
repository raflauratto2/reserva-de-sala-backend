from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from app.graphql.schema import schema

app = FastAPI(
    title="Sistema de Reservas API",
    description="API para gerenciamento de reservas com GraphQL",
    version="1.0.0",
    docs_url=None,  # Desabilita o Swagger UI
    redoc_url=None  # Desabilita o ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota GraphQL com GraphiQL
graphql_app = GraphQLRouter(schema, graphiql=True)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def root():
    return {
        "message": "Sistema de Reservas API - GraphQL",
        "graphql": "/graphql"
    }

