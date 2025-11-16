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
- `nome` (String, nullable) - Nome completo do usuário
- `username` (String, NOT NULL, Unique, Index)
- `email` (String, NOT NULL, Unique, Index)
- `hashed_password` (String, NOT NULL)
- `admin` (Boolean, NOT NULL, default=False) - Indica se o usuário é administrador
- `created_at` (DateTime)

#### Tabela `salas`
- `id` (Integer, Primary Key, Index)
- `nome` (String, NOT NULL, Index)
- `local` (String, NOT NULL)
- `capacidade` (Integer, nullable)
- `descricao` (Text, nullable)
- `criador_id` (Integer, NOT NULL, Foreign Key → usuarios.id)
- `ativa` (Boolean, NOT NULL, default=True)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Constraints:**
- Foreign key: `criador_id` referencia `usuarios.id`

#### Tabela `reservas`
- `id` (Integer, Primary Key, Index)
- `local` (String, nullable) - Mantido para compatibilidade
- `sala` (String, nullable) - Mantido para compatibilidade
- `sala_id` (Integer, nullable, Foreign Key → salas.id) - Referência à sala cadastrada
- `data_hora_inicio` (DateTime, NOT NULL)
- `data_hora_fim` (DateTime, NOT NULL)
- `responsavel_id` (Integer, NOT NULL, Foreign Key → usuarios.id)
- `cafe_quantidade` (Integer, nullable)
- `cafe_descricao` (Text, nullable)
- `link_meet` (String, nullable) - Link da sala de meet (URL)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Constraints:**
- Check constraint: `data_hora_fim > data_hora_inicio`
- Foreign key: `responsavel_id` referencia `usuarios.id`
- Foreign key: `sala_id` referencia `salas.id`

#### Tabela `reserva_participantes`
- `id` (Integer, Primary Key, Index)
- `reserva_id` (Integer, NOT NULL, Foreign Key → reservas.id)
- `usuario_id` (Integer, NOT NULL, Foreign Key → usuarios.id)
- `notificado` (Boolean, NOT NULL, default=False) - Se o participante foi notificado
- `visto` (Boolean, NOT NULL, default=False) - Se o usuário já viu a notificação
- `created_at` (DateTime)

**Constraints:**
- Foreign key: `reserva_id` referencia `reservas.id`
- Foreign key: `usuario_id` referencia `usuarios.id`
- Check constraint: garante que reserva_id e usuario_id não sejam nulos

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
    nome: "Usuário Teste"
    username: "usuario_teste"
    email: "teste@example.com"
    password: "senha123"
  }) {
    id
    nome
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

#### Reservas

```graphql
# Listar reservas
query {
  reservas(skip: 0, limit: 10) {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavel {
      id
      nome
      username
      email
    }
    linkMeet
    cafeQuantidade
    cafeDescricao
  }
}

# Obter reserva específica
query {
  reserva(reservaId: 1) {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavel {
      id
      nome
      username
    }
    linkMeet
  }
}

# Listar reservas por sala e data
query {
  reservasPorSala(salaId: 1, data: "2024-01-15", skip: 0, limit: 10) {
    id
    dataHoraInicio
    dataHoraFim
    responsavel {
      nome
    }
  }
}

# Verificar disponibilidade
query {
  verificarDisponibilidade(
    salaId: 1
    dataHoraInicio: "2024-01-15T10:00:00"
    dataHoraFim: "2024-01-15T12:00:00"
  )
}

# Obter horários disponíveis
query {
  horariosDisponiveis(
    salaId: 1
    data: "2024-01-15"
    horaInicio: "08:00:00"
    horaFim: "18:00:00"
  ) {
    inicio
    fim
  }
}

# Obter horários disponíveis por hora
query {
  horariosDisponiveisPorHora(
    salaId: 1
    data: "2024-01-15"
    horaInicio: "08:00:00"
    horaFim: "18:00:00"
  )
}

# Meu histórico de reservas
query {
  meuHistorico(apenasFuturas: false, apenasPassadas: false, skip: 0, limit: 10) {
    reserva {
      id
      sala
      dataHoraInicio
      dataHoraFim
    }
    souResponsavel
  }
}
```

#### Salas

```graphql
# Listar salas
query {
  salas(skip: 0, limit: 10, apenasAtivas: true) {
    id
    nome
    local
    capacidade
    descricao
    ativa
  }
}

# Obter sala específica
query {
  sala(salaId: 1) {
    id
    nome
    local
    capacidade
    descricao
    ativa
  }
}

# Minhas salas (criadas por mim)
query {
  minhasSalas(skip: 0, limit: 10) {
    id
    nome
    local
    capacidade
  }
}
```

#### Usuários

```graphql
# Meu perfil
query {
  meuPerfil {
    id
    nome
    username
    email
    admin
  }
}

# Listar usuários (apenas admin)
query {
  usuarios(skip: 0, limit: 10) {
    id
    nome
    username
    email
    admin
  }
}

# Obter usuário específico (apenas admin)
query {
  usuario(usuarioId: 1) {
    id
    nome
    username
    email
    admin
  }
}

# Listar usuários não admin (para seleção de participantes)
query {
  usuariosNaoAdmin(skip: 0, limit: 10) {
    id
    nome
    username
    email
  }
}
```

#### Participantes

```graphql
# Listar participantes de uma reserva
query {
  participantesReserva(reservaId: 1) {
    id
    usuario {
      id
      nome
      username
      email
    }
    notificado
    visto
  }
}

# Minhas reservas convidadas
query {
  minhasReservasConvidadas(
    apenasNaoNotificadas: false
    apenasNaoVistas: false
    skip: 0
    limit: 10
  ) {
    id
    reserva {
      id
      sala
      dataHoraInicio
      dataHoraFim
      responsavel {
        nome
      }
    }
    notificado
    visto
  }
}

# Contar reservas não vistas
query {
  contarReservasNaoVistas
}
```

### Mutations

#### Autenticação

```graphql
# Criar usuário
mutation {
  criarUsuario(usuario: {
    nome: "João Silva"
    username: "joao"
    email: "joao@example.com"
    password: "senha123"
  }) {
    id
    username
    email
  }
}

# Login
mutation {
  login(loginData: {
    username: "joao"
    password: "senha123"
  }) {
    accessToken
    tokenType
  }
}

# Atualizar perfil
mutation {
  atualizarPerfil(usuario: {
    nome: "João Silva Santos"
    email: "joao.silva@example.com"
    password: "novaSenha123"
  }) {
    id
    nome
    email
  }
}
```

#### Reservas

```graphql
# Criar reserva
mutation {
  criarReserva(reserva: {
    salaId: 1
    dataHoraInicio: "2024-01-15T10:00:00"
    dataHoraFim: "2024-01-15T12:00:00"
    cafeQuantidade: 10
    cafeDescricao: "Café expresso"
    linkMeet: "https://meet.google.com/xxx-yyyy-zzz"
  }) {
    id
    salaId
    dataHoraInicio
    dataHoraFim
  }
}

# Atualizar reserva
mutation {
  atualizarReserva(reservaId: 1, reserva: {
    dataHoraInicio: "2024-01-15T11:00:00"
    dataHoraFim: "2024-01-15T13:00:00"
    linkMeet: "https://meet.google.com/aaa-bbbb-ccc"
  }) {
    id
    dataHoraInicio
    dataHoraFim
  }
}

# Deletar reserva
mutation {
  deletarReserva(reservaId: 1)
}
```

#### Salas (apenas administradores)

```graphql
# Criar sala
mutation {
  criarSala(sala: {
    nome: "Sala de Reuniões A"
    local: "Edifício Principal - 3º Andar"
    capacidade: 20
    descricao: "Sala equipada com projetor e sistema de som"
  }) {
    id
    nome
    local
    capacidade
  }
}

# Atualizar sala
mutation {
  atualizarSala(salaId: 1, sala: {
    nome: "Sala de Reuniões A - Atualizada"
    capacidade: 25
    ativa: true
  }) {
    id
    nome
    capacidade
    ativa
  }
}

# Deletar sala
mutation {
  deletarSala(salaId: 1)
}
```

#### Participantes

```graphql
# Adicionar participante a uma reserva
mutation {
  adicionarParticipante(reservaId: 1, usuarioId: 2) {
    id
    usuario {
      nome
      email
    }
    notificado
  }
}

# Remover participante de uma reserva
mutation {
  removerParticipante(reservaId: 1, usuarioId: 2)
}

# Marcar reserva como notificada
mutation {
  marcarReservaComoNotificada(reservaId: 1)
}

# Marcar reserva como vista
mutation {
  marcarReservaComoVista(reservaId: 1)
}
```

#### Usuários (apenas administradores)

```graphql
# Criar usuário (admin)
mutation {
  criarUsuarioAdmin(usuario: {
    nome: "Maria Santos"
    username: "maria"
    email: "maria@example.com"
    password: "senha123"
    admin: false
  }) {
    id
    username
    admin
  }
}

# Atualizar usuário (admin)
mutation {
  atualizarUsuarioAdmin(usuarioId: 1, usuario: {
    nome: "Maria Santos Silva"
    email: "maria.silva@example.com"
    admin: true
  }) {
    id
    nome
    admin
  }
}

# Deletar usuário (admin)
mutation {
  deletarUsuario(usuarioId: 1)
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

## Funcionalidades Principais

### Sistema de Salas
- **Criação e gerenciamento de salas**: Apenas administradores podem criar, editar e deletar salas
- **Salas ativas/inativas**: Possibilidade de desativar salas sem deletá-las
- **Reservas por sala**: As reservas podem ser vinculadas a salas cadastradas

### Sistema de Participantes
- **Convites para reservas**: O responsável pode adicionar participantes às reservas
- **Notificações**: Sistema de notificação para participantes
- **Controle de visualização**: Rastreamento de quais participantes viram as notificações
- **Restrições**: Administradores não podem ser adicionados como participantes

### Validações e Regras
- **Conflitos de horário**: O sistema valida automaticamente conflitos de horário para a mesma sala
- **Permissões de edição**: Apenas o responsável que criou a reserva pode editá-la ou deletá-la
- **Validação de datas**: Garante que a data/hora de fim seja posterior à data/hora de início
- **Verificação de disponibilidade**: Queries para verificar horários disponíveis antes de criar reservas

### Histórico e Consultas
- **Histórico pessoal**: Cada usuário pode ver todas as reservas em que participou (como responsável ou participante)
- **Filtros temporais**: Possibilidade de filtrar reservas futuras ou passadas
- **Reservas por data**: Consulta de reservas de uma sala em uma data específica
- **Horários disponíveis**: Lista de horários livres em uma sala para uma data específica

## Notas Importantes

- As credenciais padrão estão no `docker-compose.yml` (altere em produção!)
- A `SECRET_KEY` deve ser alterada em produção
- Apenas o responsável que criou a reserva pode editá-la ou deletá-la
- O sistema valida conflitos de horário automaticamente
- Apenas administradores podem criar, editar e deletar salas
- Administradores não podem ser adicionados como participantes de reservas
- O campo `sala_id` é preferencial; os campos `local` e `sala` são mantidos apenas para compatibilidade

