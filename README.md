# Sistema de Reservas

Backend em Python para gerenciamento de reservas com validação de conflitos de horários. O projeto utiliza GraphQL como API principal.

## Tecnologias

- **Python 3.11**
- **FastAPI** - Framework web
- **Strawberry GraphQL** - API GraphQL
- **SQLAlchemy** - ORM
- **PostgreSQL** - Banco de dados
- **Alembic** - Migrações
- **Docker & Docker Compose** - Containerização

## Requisitos

- Docker e Docker Compose instalados
- Python 3.11+ (opcional, para rodar localmente)

## Configuração e Execução

### Passo 1: Subir os containers

```bash
docker compose up -d
```

Aguarde alguns segundos e verifique o status:

```bash
docker compose ps
```

### Passo 2: Criar as tabelas e colunas

Execute as migrações para criar as tabelas no banco de dados:

```bash
docker compose exec api alembic upgrade head
```

Este comando cria as seguintes tabelas e colunas:

#### Tabela `usuarios`
- `id` (Integer, Primary Key, Index)
- `username` (String, NOT NULL, Unique, Index)
- `email` (String, NOT NULL, Unique, Index)
- `hashed_password` (String, NOT NULL)
- `created_at` (DateTime)

#### Tabela `reservas`
- `id` (Integer, Primary Key, Index)
- `local` (String, NOT NULL)
- `sala` (String, NOT NULL)
- `data_hora_inicio` (DateTime, NOT NULL)
- `data_hora_fim` (DateTime, NOT NULL)
- `responsavel_id` (Integer, NOT NULL, Foreign Key → usuarios.id)
- `cafe_quantidade` (Integer, nullable)
- `cafe_descricao` (Text, nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Constraints:**
- Check constraint: `data_hora_fim > data_hora_inicio`
- Foreign key: `responsavel_id` referencia `usuarios.id`

### Passo 3: Verificar a API

Acesse no navegador:
- **GraphiQL**: http://localhost:8000/graphql
- **Endpoint raiz**: http://localhost:8000

## Informações de Conexão

**PostgreSQL:**
- Host: `localhost`
- Porta: `5432`
- Database: `reservas_db`
- Usuário: `reservas_user`
- Senha: `reservas_pass`

**API:**
- URL: `http://localhost:8000`
- GraphiQL: `http://localhost:8000/graphql`

## Comandos Úteis

```bash
# Ver logs
docker compose logs -f

# Parar containers
docker compose down

# Parar e remover volumes
docker compose down -v

# Reiniciar
docker compose restart

# Status
docker compose ps

# Criar usuário administrador
docker compose exec api python create_admin.py admin admin@example.com senha123
```

## Criar Usuário Administrador

Para criar um usuário administrador (necessário para criar, editar e deletar salas):

```bash
# Dentro do container Docker
docker compose exec api python create_admin.py <username> <email> <password>

# Exemplo:
docker compose exec api python create_admin.py admin admin@example.com senha123
```

**Importante:**
- Apenas usuários administradores podem criar, editar e deletar salas
- Usuários criados via GraphQL (`criarUsuario`) **não** são administradores por padrão
- O primeiro usuário admin deve ser criado manualmente usando o script

## Rodando Localmente (Sem Docker)

1. **Instalar PostgreSQL e criar banco:**
```sql
CREATE DATABASE reservas_db;
CREATE USER reservas_user WITH PASSWORD 'reservas_pass';
GRANT ALL PRIVILEGES ON DATABASE reservas_db TO reservas_user;
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente:**

Crie um arquivo `.env`:
```env
DATABASE_URL=postgresql://reservas_user:reservas_pass@localhost:5432/reservas_db
SECRET_KEY=sua-chave-secreta-aqui
```

Ou exporte (Windows PowerShell):
```powershell
$env:DATABASE_URL="postgresql://reservas_user:reservas_pass@localhost:5432/reservas_db"
$env:SECRET_KEY="sua-chave-secreta-aqui"
```

Ou exporte (Linux/Mac):
```bash
export DATABASE_URL=postgresql://reservas_user:reservas_pass@localhost:5432/reservas_db
export SECRET_KEY=sua-chave-secreta-aqui
```

4. **Executar migrações:**
```bash
alembic upgrade head
```

5. **Rodar a API:**
```bash
uvicorn app.main:app --reload
```

## Autenticação

O sistema utiliza JWT para autenticação. Todas as requisições GraphQL requerem o header:
```
Authorization: Bearer <seu_token>
```

### Registrar usuário
```graphql
mutation {
  criarUsuario(usuario: {
    username: "usuario_teste"
    email: "teste@example.com"
    password: "senha123"
  }) {
    id
    username
    email
  }
}
```

### Login
```graphql
mutation {
  login(loginData: {
    username: "usuario_teste"
    password: "senha123"
  }) {
    accessToken
    tokenType
  }
}
```

## GraphQL

### Queries

```graphql
# Listar reservas
query {
  reservas(skip: 0, limit: 10) {
    id
    local
    sala
    dataHoraInicio
    dataHoraFim
  }
}

# Obter reserva específica
query {
  reserva(reservaId: 1) {
    id
    local
    sala
  }
}
```

### Mutations

```graphql
# Criar reserva
mutation {
  criarReserva(reserva: {
    local: "Edifício A"
    sala: "Sala 101"
    dataHoraInicio: "2024-01-15T10:00:00"
    dataHoraFim: "2024-01-15T12:00:00"
  }) {
    id
    local
    sala
  }
}

# Atualizar reserva
mutation {
  atualizarReserva(reservaId: 1, reserva: {
    local: "Edifício B"
  }) {
    id
    local
  }
}

# Deletar reserva
mutation {
  deletarReserva(reservaId: 1)
}
```

## Migrações

### Criar nova migração
```bash
docker compose exec api alembic revision --autogenerate -m "descricao"
```

### Aplicar migrações
```bash
docker compose exec api alembic upgrade head
```

### Reverter migração
```bash
docker compose exec api alembic downgrade -1
```

## Notas Importantes

- As credenciais padrão estão no `docker-compose.yml` (altere em produção!)
- A `SECRET_KEY` deve ser alterada em produção
- Apenas o responsável que criou a reserva pode editá-la ou deletá-la
- O sistema valida conflitos de horário automaticamente

