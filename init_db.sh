#!/bin/bash
# Script para inicializar o banco de dados
# Execute após subir os containers com: docker compose exec api bash init_db.sh

echo "Executando migrações..."
alembic upgrade head

echo "Banco de dados inicializado com sucesso!"

