# Documentação da API - Frontend

Documentação completa das rotas GraphQL para integração com o frontend.

## URL Base

```
http://localhost:8000/graphql
```

## CORS (Cross-Origin Resource Sharing)

O backend está configurado para aceitar requisições das seguintes origens:

- `http://localhost:3000` (Vite padrão)
- `http://localhost:5173` (Vite porta alternativa)
- `http://localhost:5174` (Vite porta alternativa)
- `http://localhost:8080` (Vue CLI padrão)
- `http://localhost:4200` (Angular padrão)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:5174`

**Verificação rápida:** Teste a API diretamente no navegador: `http://localhost:8000/graphql` — se abrir o GraphiQL, a API está funcionando.

Se você estiver usando uma porta diferente do frontend, será necessário adicionar essa porta na lista de `allow_origins` no arquivo `app/main.py`.

## Autenticação

Todas as requisições (exceto `criarUsuario` e `login`) requerem o header de autenticação:

```
Authorization: Bearer <token>
```

O token é obtido através da mutation `login` e deve ser armazenado no frontend (localStorage, sessionStorage, etc.).

## Fluxo Rápido: Reservar uma Sala

**Fluxo principal para reservar uma sala por hora:**

1. **Listar salas disponíveis:** `salas(apenasAtivas: true)`
2. **Usuário seleciona uma sala e uma data**
3. **Buscar horários disponíveis:** `horariosDisponiveisPorHora(salaId, data)` → retorna `["08:00", "09:00", "10:00", ...]`
4. **Usuário seleciona uma hora** (ex: "14:00")
5. **Criar reserva:** `criarReserva` com `dataHoraInicio: "2024-01-20T14:00:00"` e `dataHoraFim: "2024-01-20T15:00:00"`

**Nota:** Cada reserva é de **1 hora**. Se o usuário selecionar "14:00", a reserva será das 14:00 às 15:00.

---

## 1. Autenticação

### 1.1. Registrar Usuário

**Mutation:** `criarUsuario`

**Autenticação:** Não requerida

**Request:**
```graphql
mutation {
  criarUsuario(usuario: {
    nome: "João Silva"
    username: "usuario_teste"
    email: "teste@example.com"
    password: "senha123"
  }) {
    id
    nome
    username
    email
    createdAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: `
      mutation {
        criarUsuario(usuario: {
          nome: "João Silva"
          username: "usuario_teste"
          email: "teste@example.com"
          password: "senha123"
        }) {
          id
          nome
          username
          email
          createdAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "criarUsuario": {
      "id": 1,
      "nome": "João Silva",
      "username": "usuario_teste",
      "email": "teste@example.com",
      "createdAt": "2024-01-15T10:00:00"
    }
  }
}
```

**Erros Possíveis:**
- `"Username já está em uso"` - Username já existe
- `"Email já está em uso"` - Email já existe
- `"A senha não pode ter mais de 72 caracteres"` - Senha muito longa

**Campos Obrigatórios:**
- `username` (String) - Nome de usuário único
- `email` (String) - Email único
- `password` (String) - Senha do usuário

**Campos Opcionais:**
- `nome` (String) - Nome completo do usuário (opcional)

---

### 1.2. Login

**Mutation:** `login`

**Autenticação:** Não requerida

**Request:**
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

**Exemplo HTTP (fetch):**
```javascript
const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: `
      mutation {
        login(loginData: {
          username: "usuario_teste"
          password: "senha123"
        }) {
          accessToken
          tokenType
        }
      }
    `
  })
});

const data = await response.json();
// Armazenar o token: localStorage.setItem('token', data.data.login.accessToken);
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "login": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

**Erros Possíveis:**
- `"Username ou senha incorretos"` - Credenciais inválidas
- `"A senha não pode ter mais de 72 caracteres"` - Senha muito longa

---

## 2. Queries (Consultas)

### 2.1. Listar Reservas

**Query:** `reservas`

**Autenticação:** Requerida

**Parâmetros:**
- `skip` (opcional, padrão: 0) - Número de registros para pular (paginação)
- `limit` (opcional, padrão: 100) - Número máximo de registros a retornar

**Request:**
```graphql
query {
  reservas(skip: 0, limit: 10) {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        reservas(skip: 0, limit: 10) {
          id
          local
          sala
          dataHoraInicio
          dataHoraFim
          responsavelId
          cafeQuantidade
          cafeDescricao
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "reservas": [
      {
        "id": 1,
        "local": "Edifício A",
        "sala": "Sala 101",
        "dataHoraInicio": "2024-01-15T10:00:00",
        "dataHoraFim": "2024-01-15T12:00:00",
        "responsavelId": 1,
        "cafeQuantidade": 10,
        "cafeDescricao": "Café expresso",
        "createdAt": "2024-01-15T09:00:00",
        "updatedAt": "2024-01-15T09:00:00"
      }
    ]
  }
}
```

---

### 2.2. Obter Reserva por ID

**Query:** `reserva`

**Autenticação:** Requerida

**Parâmetros:**
- `reservaId` (obrigatório) - ID da reserva

**Request:**
```graphql
query {
  reserva(reservaId: 1) {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        reserva(reservaId: 1) {
          id
          local
          sala
          dataHoraInicio
          dataHoraFim
          responsavelId
          cafeQuantidade
          cafeDescricao
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "reserva": {
      "id": 1,
      "local": "Edifício A",
      "sala": "Sala 101",
      "dataHoraInicio": "2024-01-15T10:00:00",
      "dataHoraFim": "2024-01-15T12:00:00",
      "responsavelId": 1,
      "cafeQuantidade": 10,
      "cafeDescricao": "Café expresso",
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T09:00:00"
    }
  }
}
```

**Resposta quando não encontrada:**
```json
{
  "data": {
    "reserva": null
  }
}
```

---

### 2.3. Listar Salas

**Query:** `salas`

**Autenticação:** Requerida

**Parâmetros:**
- `skip` (opcional, padrão: 0) - Número de registros para pular (paginação)
- `limit` (opcional, padrão: 100) - Número máximo de registros a retornar
- `apenasAtivas` (opcional, padrão: false) - Se true, retorna apenas salas ativas

**Request:**
```graphql
query {
  salas(skip: 0, limit: 10, apenasAtivas: true) {
    id
    nome
    local
    capacidade
    descricao
    criadorId
    ativa
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        salas(skip: 0, limit: 10, apenasAtivas: true) {
          id
          nome
          local
          capacidade
          descricao
          criadorId
          ativa
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "salas": [
      {
        "id": 1,
        "nome": "Sala de Reuniões 1",
        "local": "Edifício A",
        "capacidade": 10,
        "descricao": "Sala com projetor e quadro branco",
        "criadorId": 1,
        "ativa": true,
        "createdAt": "2024-01-15T09:00:00",
        "updatedAt": "2024-01-15T09:00:00"
      }
    ]
  }
}
```

---

### 2.4. Obter Sala por ID

**Query:** `sala`

**Autenticação:** Requerida

**Parâmetros:**
- `salaId` (obrigatório) - ID da sala

**Request:**
```graphql
query {
  sala(salaId: 1) {
    id
    nome
    local
    capacidade
    descricao
    criadorId
    ativa
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        sala(salaId: 1) {
          id
          nome
          local
          capacidade
          descricao
          criadorId
          ativa
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "sala": {
      "id": 1,
      "nome": "Sala de Reuniões 1",
      "local": "Edifício A",
      "capacidade": 10,
      "descricao": "Sala com projetor e quadro branco",
      "criadorId": 1,
      "ativa": true,
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T09:00:00"
    }
  }
}
```

**Resposta quando não encontrada:**
```json
{
  "data": {
    "sala": null
  }
}
```

---

### 2.5. Listar Minhas Salas

**Query:** `minhasSalas`

**Autenticação:** Requerida

**Parâmetros:**
- `skip` (opcional, padrão: 0) - Número de registros para pular (paginação)
- `limit` (opcional, padrão: 100) - Número máximo de registros a retornar

**Request:**
```graphql
query {
  minhasSalas(skip: 0, limit: 10) {
    id
    nome
    local
    capacidade
    descricao
    criadorId
    ativa
    createdAt
    updatedAt
  }
}
```

---

### 2.6. Obter Meu Perfil

**Query:** `meuPerfil`

**Autenticação:** Requerida

**Descrição:** Retorna o perfil do usuário atual, incluindo se é administrador.

**Request:**
```graphql
query {
  meuPerfil {
    id
    nome
    username
    email
    admin
    createdAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        meuPerfil {
          id
          nome
          username
          email
          admin
          createdAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "meuPerfil": {
      "id": 1,
      "nome": "Administrador",
      "username": "admin",
      "email": "admin@example.com",
      "admin": true,
      "createdAt": "2024-01-15T09:00:00"
    }
  }
}
```

**Uso:** Use esta query para verificar se o usuário atual é administrador e mostrar/ocultar funcionalidades de administração no frontend.

---

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        minhasSalas(skip: 0, limit: 10) {
          id
          nome
          local
          capacidade
          descricao
          criadorId
          ativa
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "minhasSalas": [
      {
        "id": 1,
        "nome": "Sala de Reuniões 1",
        "local": "Edifício A",
        "capacidade": 10,
        "descricao": "Sala com projetor e quadro branco",
        "criadorId": 1,
        "ativa": true,
        "createdAt": "2024-01-15T09:00:00",
        "updatedAt": "2024-01-15T09:00:00"
      }
    ]
  }
}
```

---

### 2.7. Listar Reservas de uma Sala em uma Data

**Query:** `reservasPorSala`

**Autenticação:** Requerida

**Parâmetros:**
- `salaId` (obrigatório) - ID da sala
- `data` (obrigatório) - Data no formato "YYYY-MM-DD"

**Request:**
```graphql
query {
  reservasPorSala(salaId: 1, data: "2024-01-15") {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        reservasPorSala(salaId: 1, data: "2024-01-15") {
          id
          local
          sala
          salaId
          dataHoraInicio
          dataHoraFim
          responsavelId
          cafeQuantidade
          cafeDescricao
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "reservasPorSala": [
      {
        "id": 1,
        "local": "Edifício A",
        "sala": null,
        "salaId": 1,
        "dataHoraInicio": "2024-01-15T10:00:00",
        "dataHoraFim": "2024-01-15T12:00:00",
        "responsavelId": 1,
        "cafeQuantidade": 10,
        "cafeDescricao": "Café expresso",
        "createdAt": "2024-01-15T09:00:00",
        "updatedAt": "2024-01-15T09:00:00"
      }
    ]
  }
}
```

---

### 2.8. Obter Horários Disponíveis de uma Sala

**Query:** `horariosDisponiveis`

**Autenticação:** Requerida

**Parâmetros:**
- `salaId` (obrigatório) - ID da sala
- `data` (obrigatório) - Data no formato "YYYY-MM-DD"
- `horaInicio` (opcional, padrão: "08:00:00") - Hora de início no formato "HH:MM:SS"
- `horaFim` (opcional, padrão: "18:00:00") - Hora de fim no formato "HH:MM:SS"

**Request:**
```graphql
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
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
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
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "horariosDisponiveis": [
      {
        "inicio": "2024-01-15T08:00:00",
        "fim": "2024-01-15T10:00:00"
      },
      {
        "inicio": "2024-01-15T12:00:00",
        "fim": "2024-01-15T18:00:00"
      }
    ]
  }
}
```

**Explicação:** Esta query retorna uma lista de intervalos de horários disponíveis. No exemplo acima, a sala está disponível:
- Das 08:00 às 10:00
- Das 12:00 às 18:00

Isso significa que há reservas das 10:00 às 12:00.

---

### 2.9. Obter Horários Disponíveis por Hora (Slots de 1 hora)

**Query:** `horariosDisponiveisPorHora`

**Autenticação:** Requerida

**Descrição:** Retorna uma lista de horários disponíveis em formato de slots de 1 hora. Ideal para quando o usuário precisa selecionar uma hora específica para reservar (ex: 08:00, 09:00, 10:00).

**Parâmetros:**
- `salaId` (obrigatório) - ID da sala
- `data` (obrigatório) - Data no formato "YYYY-MM-DD"
- `horaInicio` (opcional, padrão: "08:00:00") - Hora de início no formato "HH:MM:SS"
- `horaFim` (opcional, padrão: "18:00:00") - Hora de fim no formato "HH:MM:SS"

**Request:**
```graphql
query {
  horariosDisponiveisPorHora(
    salaId: 1
    data: "2024-01-15"
    horaInicio: "08:00:00"
    horaFim: "18:00:00"
  )
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        horariosDisponiveisPorHora(
          salaId: 1
          data: "2024-01-15"
          horaInicio: "08:00:00"
          horaFim: "18:00:00"
        )
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "horariosDisponiveisPorHora": [
      "08:00",
      "09:00",
      "10:00",
      "12:00",
      "13:00",
      "14:00",
      "15:00",
      "16:00",
      "17:00"
    ]
  }
}
```

**Explicação:** Esta query retorna uma lista de horas disponíveis. No exemplo acima, as horas disponíveis são: 08:00, 09:00, 10:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00. Isso significa que:
- A hora 11:00 está ocupada (não aparece na lista)
- Cada hora representa um slot de 1 hora disponível para reserva

**Uso:** Quando o usuário selecionar uma sala e uma data, use esta query para mostrar apenas as horas disponíveis. O usuário pode então clicar em uma hora para fazer a reserva.

---

### 2.10. Verificar Disponibilidade de um Horário Específico

**Query:** `verificarDisponibilidade`

**Autenticação:** Requerida

**Parâmetros:**
- `salaId` (obrigatório) - ID da sala
- `dataHoraInicio` (obrigatório) - Data/hora de início no formato ISO 8601: "YYYY-MM-DDTHH:mm:ss"
- `dataHoraFim` (obrigatório) - Data/hora de fim no formato ISO 8601: "YYYY-MM-DDTHH:mm:ss"

**Request:**
```graphql
query {
  verificarDisponibilidade(
    salaId: 1
    dataHoraInicio: "2024-01-15T14:00:00"
    dataHoraFim: "2024-01-15T16:00:00"
  )
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      query {
        verificarDisponibilidade(
          salaId: 1
          dataHoraInicio: "2024-01-15T14:00:00"
          dataHoraFim: "2024-01-15T16:00:00"
        )
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso (disponível):**
```json
{
  "data": {
    "verificarDisponibilidade": true
  }
}
```

**Resposta (ocupado):**
```json
{
  "data": {
    "verificarDisponibilidade": false
  }
}
```

---

## 3. Mutations (Modificações)

### 3.1. Criar Reserva

**Mutation:** `criarReserva`

**Autenticação:** Requerida

**Request (usando salaId - recomendado):**
```graphql
mutation {
  criarReserva(reserva: {
    salaId: 1
    dataHoraInicio: "2024-01-15T10:00:00"
    dataHoraFim: "2024-01-15T12:00:00"
    cafeQuantidade: 10
    cafeDescricao: "Café expresso"
  }) {
    id
    local
    sala
    salaId
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Request (usando local e sala - compatibilidade):**
```graphql
mutation {
  criarReserva(reserva: {
    local: "Edifício A"
    sala: "Sala 101"
    dataHoraInicio: "2024-01-15T10:00:00"
    dataHoraFim: "2024-01-15T12:00:00"
    cafeQuantidade: 10
    cafeDescricao: "Café expresso"
  }) {
    id
    local
    sala
    salaId
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        criarReserva(reserva: {
          local: "Edifício A"
          sala: "Sala 101"
          dataHoraInicio: "2024-01-15T10:00:00"
          dataHoraFim: "2024-01-15T12:00:00"
          cafeQuantidade: 10
          cafeDescricao: "Café expresso"
        }) {
          id
          local
          sala
          dataHoraInicio
          dataHoraFim
          responsavelId
          cafeQuantidade
          cafeDescricao
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "criarReserva": {
      "id": 1,
      "local": "Edifício A",
      "sala": "Sala 101",
      "dataHoraInicio": "2024-01-15T10:00:00",
      "dataHoraFim": "2024-01-15T12:00:00",
      "responsavelId": 1,
      "cafeQuantidade": 10,
      "cafeDescricao": "Café expresso",
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T09:00:00"
    }
  }
}
```

**Erros Possíveis:**
- `"Conflito de horário: já existe uma reserva para esta sala no período especificado"` - Conflito de horário
- `"A data/hora de fim deve ser maior que a data/hora de início"` - Data inválida
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido

**Campos Obrigatórios:**
- `dataHoraInicio` (DateTime - formato ISO 8601: "YYYY-MM-DDTHH:mm:ss")
- `dataHoraFim` (DateTime - formato ISO 8601: "YYYY-MM-DDTHH:mm:ss")
- **OU** `salaId` (Integer) **OU** `sala` (String) - Use `salaId` quando possível

**Campos Opcionais:**
- `local` (String) - Opcional quando usar `salaId`
- `sala` (String) - Opcional quando usar `salaId`
- `salaId` (Integer) - ID da sala (preferencial)
- `cafeQuantidade` (Integer)
- `cafeDescricao` (String)

**Nota:** É recomendado usar `salaId` ao invés de `sala` (string) para garantir consistência e melhor validação de conflitos.

**Importante sobre Reservas por Hora:**
- As reservas são feitas em slots de **1 hora** (ex: 08:00-09:00, 09:00-10:00)
- Use a query `horariosDisponiveisPorHora` para obter apenas as horas disponíveis
- Quando o usuário selecionar uma hora (ex: "14:00"), a reserva será das 14:00 às 15:00
- O horário de fim é sempre 1 hora após o horário de início

---

### 3.2. Atualizar Reserva

**Mutation:** `atualizarReserva`

**Autenticação:** Requerida

**Observação:** Apenas o usuário que criou a reserva pode atualizá-la.

**Request:**
```graphql
mutation {
  atualizarReserva(
    reservaId: 1
    reserva: {
      local: "Edifício B"
      sala: "Sala 202"
      dataHoraInicio: "2024-01-15T14:00:00"
      dataHoraFim: "2024-01-15T16:00:00"
      cafeQuantidade: 15
      cafeDescricao: "Café e água"
    }
  ) {
    id
    local
    sala
    salaId
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
    cafeDescricao
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        atualizarReserva(
          reservaId: 1
          reserva: {
            local: "Edifício B"
            sala: "Sala 202"
            dataHoraInicio: "2024-01-15T14:00:00"
            dataHoraFim: "2024-01-15T16:00:00"
            cafeQuantidade: 15
            cafeDescricao: "Café e água"
          }
        ) {
          id
          local
          sala
          dataHoraInicio
          dataHoraFim
          responsavelId
          cafeQuantidade
          cafeDescricao
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "atualizarReserva": {
      "id": 1,
      "local": "Edifício B",
      "sala": "Sala 202",
      "dataHoraInicio": "2024-01-15T14:00:00",
      "dataHoraFim": "2024-01-15T16:00:00",
      "responsavelId": 1,
      "cafeQuantidade": 15,
      "cafeDescricao": "Café e água",
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T10:30:00"
    }
  }
}
```

**Resposta quando não encontrada ou sem permissão:**
```json
{
  "data": {
    "atualizarReserva": null
  }
}
```

**Erros Possíveis:**
- `"Conflito de horário: já existe uma reserva para esta sala no período especificado"` - Conflito de horário
- `"A data/hora de fim deve ser maior que a data/hora de início"` - Data inválida
- `"Reserva não encontrada"` - Reserva não existe
- `"Você não tem permissão para atualizar esta reserva"` - Sem permissão
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido

**Campos Opcionais (todos podem ser omitidos):**
- `local` (String)
- `sala` (String)
- `salaId` (Integer) - ID da sala (preferencial)
- `dataHoraInicio` (DateTime)
- `dataHoraFim` (DateTime)
- `cafeQuantidade` (Integer)
- `cafeDescricao` (String)

**Nota:** Apenas os campos fornecidos serão atualizados. Os demais permanecem inalterados.

---

### 3.3. Deletar Reserva

**Mutation:** `deletarReserva`

**Autenticação:** Requerida

**Observação:** Apenas o usuário que criou a reserva pode deletá-la.

**Request:**
```graphql
mutation {
  deletarReserva(reservaId: 1)
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        deletarReserva(reservaId: 1)
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "deletarReserva": true
  }
}
```

**Resposta quando não encontrada ou sem permissão:**
```json
{
  "data": {
    "deletarReserva": false
  }
}
```

**Erros Possíveis:**
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido

---

### 3.4. Criar Sala

**Mutation:** `criarSala`

**Autenticação:** Requerida

**Permissão:** Apenas administradores podem criar salas.

**Request:**
```graphql
mutation {
  criarSala(sala: {
    nome: "Sala de Reuniões 1"
    local: "Edifício A"
    capacidade: 10
    descricao: "Sala com projetor e quadro branco"
  }) {
    id
    nome
    local
    capacidade
    descricao
    criadorId
    ativa
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        criarSala(sala: {
          nome: "Sala de Reuniões 1"
          local: "Edifício A"
          capacidade: 10
          descricao: "Sala com projetor e quadro branco"
        }) {
          id
          nome
          local
          capacidade
          descricao
          criadorId
          ativa
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "criarSala": {
      "id": 1,
      "nome": "Sala de Reuniões 1",
      "local": "Edifício A",
      "capacidade": 10,
      "descricao": "Sala com projetor e quadro branco",
      "criadorId": 1,
      "ativa": true,
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T09:00:00"
    }
  }
}
```

**Erros Possíveis:**
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido
- `"Apenas administradores podem criar salas"` - Usuário não é admin

**Campos Obrigatórios:**
- `nome` (String)
- `local` (String)

**Campos Opcionais:**
- `capacidade` (Integer, mínimo: 1)
- `descricao` (String)

**Nota:** Apenas usuários com `admin: true` podem criar salas. Use a query `meuPerfil` para verificar se o usuário é admin.

---

### 3.5. Atualizar Sala

**Mutation:** `atualizarSala`

**Autenticação:** Requerida

**Permissão:** Apenas administradores podem atualizar salas.

**Request:**
```graphql
mutation {
  atualizarSala(
    salaId: 1
    sala: {
      nome: "Sala de Reuniões 1 - Atualizada"
      capacidade: 15
      descricao: "Sala renovada com novos equipamentos"
      ativa: true
    }
  ) {
    id
    nome
    local
    capacidade
    descricao
    criadorId
    ativa
    createdAt
    updatedAt
  }
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        atualizarSala(
          salaId: 1
          sala: {
            nome: "Sala de Reuniões 1 - Atualizada"
            capacidade: 15
            descricao: "Sala renovada com novos equipamentos"
            ativa: true
          }
        ) {
          id
          nome
          local
          capacidade
          descricao
          criadorId
          ativa
          createdAt
          updatedAt
        }
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "atualizarSala": {
      "id": 1,
      "nome": "Sala de Reuniões 1 - Atualizada",
      "local": "Edifício A",
      "capacidade": 15,
      "descricao": "Sala renovada com novos equipamentos",
      "criadorId": 1,
      "ativa": true,
      "createdAt": "2024-01-15T09:00:00",
      "updatedAt": "2024-01-15T10:30:00"
    }
  }
}
```

**Resposta quando não encontrada ou sem permissão:**
```json
{
  "data": {
    "atualizarSala": null
  }
}
```

**Erros Possíveis:**
- `"Sala não encontrada ou você não tem permissão para atualizá-la"` - Sala não existe ou usuário não é admin
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido

**Nota:** Apenas usuários com `admin: true` podem atualizar salas.

**Campos Opcionais (todos podem ser omitidos):**
- `nome` (String)
- `local` (String)
- `capacidade` (Integer, mínimo: 1)
- `descricao` (String)
- `ativa` (Boolean)

**Nota:** Apenas os campos fornecidos serão atualizados. Os demais permanecem inalterados.

---

### 3.6. Deletar Sala

**Mutation:** `deletarSala`

**Autenticação:** Requerida

**Permissão:** Apenas administradores podem deletar salas.

**Request:**
```graphql
mutation {
  deletarSala(salaId: 1)
}
```

**Exemplo HTTP (fetch):**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: `
      mutation {
        deletarSala(salaId: 1)
      }
    `
  })
});

const data = await response.json();
```

**Resposta de Sucesso:**
```json
{
  "data": {
    "deletarSala": true
  }
}
```

**Resposta quando não encontrada ou sem permissão:**
```json
{
  "data": {
    "deletarSala": false
  }
}
```

**Erros Possíveis:**
- `"Sala não encontrada ou você não tem permissão para deletá-la"` - Sala não existe ou usuário não é admin
- `"Token de autenticação não fornecido"` - Token ausente
- `"Token inválido ou expirado"` - Token inválido

**Nota:** Apenas usuários com `admin: true` podem deletar salas.

---

## 4. Estrutura de Dados

### 4.1. Tipo: UsuarioType

```typescript
interface UsuarioType {
  id: number;
  nome?: string | null; // Nome completo do usuário (opcional)
  username: string;
  email: string;
  admin: boolean; // true se o usuário é administrador
  createdAt: string; // DateTime ISO 8601
}
```

### 4.2. Tipo: ReservaType

```typescript
interface ReservaType {
  id: number;
  local?: string | null;
  sala?: string | null;
  salaId?: number | null; // ID da sala (preferencial)
  dataHoraInicio: string; // DateTime ISO 8601
  dataHoraFim: string; // DateTime ISO 8601
  responsavelId: number;
  cafeQuantidade?: number | null;
  cafeDescricao?: string | null;
  createdAt: string; // DateTime ISO 8601
  updatedAt: string; // DateTime ISO 8601
}
```

### 4.3. Tipo: SalaType

```typescript
interface SalaType {
  id: number;
  nome: string;
  local: string;
  capacidade?: number | null;
  descricao?: string | null;
  criadorId: number;
  ativa: boolean;
  createdAt: string; // DateTime ISO 8601
  updatedAt: string; // DateTime ISO 8601
}
```

### 4.4. Tipo: HorarioDisponivelType

```typescript
interface HorarioDisponivelType {
  inicio: string; // DateTime ISO 8601
  fim: string; // DateTime ISO 8601
}
```

### 4.5. Tipo: TokenType

```typescript
interface TokenType {
  accessToken: string;
  tokenType: string; // Sempre "bearer"
}
```

---

## 5. Tratamento de Erros

### 5.1. Estrutura de Erro GraphQL

```json
{
  "errors": [
    {
      "message": "Mensagem de erro aqui",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": ["criarReserva"]
    }
  ],
  "data": null
}
```

### 5.2. Códigos de Erro Comuns

| Erro | Descrição | Solução |
|------|-----------|---------|
| `"Token de autenticação não fornecido"` | Header Authorization ausente | Adicionar header `Authorization: Bearer <token>` |
| `"Token inválido ou expirado"` | Token inválido ou expirado | Fazer login novamente |
| `"Username já está em uso"` | Username duplicado | Usar outro username |
| `"Email já está em uso"` | Email duplicado | Usar outro email |
| `"Username ou senha incorretos"` | Credenciais inválidas | Verificar username e senha |
| `"Conflito de horário: já existe uma reserva para esta sala no período especificado"` | Conflito de horário | Escolher outro horário ou sala |
| `"A data/hora de fim deve ser maior que a data/hora de início"` | Data inválida | Corrigir as datas |
| `"Reserva não encontrada"` | Reserva não existe | Verificar o ID da reserva |
| `"Você não tem permissão para atualizar/deletar esta reserva"` | Sem permissão | Apenas o criador pode modificar |

---

## 6. Exemplo Completo de Integração (React)

```javascript
// api.js
const API_URL = 'http://localhost:8000/graphql';

async function graphqlRequest(query, variables = {}, token = null) {
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(API_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      query,
      variables,
    }),
  });
  
  const data = await response.json();
  
  if (data.errors) {
    throw new Error(data.errors[0].message);
  }
  
  return data.data;
}

// Autenticação
export async function criarUsuario(nome, username, email, password) {
  const query = `
    mutation CriarUsuario($usuario: UsuarioInput!) {
      criarUsuario(usuario: $usuario) {
        id
        nome
        username
        email
        createdAt
      }
    }
  `;
  
  return await graphqlRequest(query, {
    usuario: { nome, username, email, password }
  });
}

export async function login(username, password) {
  const query = `
    mutation Login($loginData: LoginInput!) {
      login(loginData: $loginData) {
        accessToken
        tokenType
      }
    }
  `;
  
  return await graphqlRequest(query, {
    loginData: { username, password }
  });
}

// Reservas
export async function listarReservas(token, skip = 0, limit = 100) {
  const query = `
    query ListarReservas($skip: Int!, $limit: Int!) {
      reservas(skip: $skip, limit: $limit) {
        id
        local
        sala
        salaId
        dataHoraInicio
        dataHoraFim
        responsavelId
        cafeQuantidade
        cafeDescricao
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { skip, limit }, token);
}

export async function obterReserva(token, reservaId) {
  const query = `
    query ObterReserva($reservaId: Int!) {
      reserva(reservaId: $reservaId) {
        id
        local
        sala
        salaId
        dataHoraInicio
        dataHoraFim
        responsavelId
        cafeQuantidade
        cafeDescricao
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { reservaId }, token);
}

export async function criarReserva(token, reserva) {
  const query = `
    mutation CriarReserva($reserva: ReservaInput!) {
      criarReserva(reserva: $reserva) {
        id
        local
        sala
        salaId
        dataHoraInicio
        dataHoraFim
        responsavelId
        cafeQuantidade
        cafeDescricao
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { reserva }, token);
}

// Salas
export async function listarSalas(token, skip = 0, limit = 100, apenasAtivas = false) {
  const query = `
    query ListarSalas($skip: Int!, $limit: Int!, $apenasAtivas: Boolean!) {
      salas(skip: $skip, limit: $limit, apenasAtivas: $apenasAtivas) {
        id
        nome
        local
        capacidade
        descricao
        criadorId
        ativa
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { skip, limit, apenasAtivas }, token);
}

export async function obterSala(token, salaId) {
  const query = `
    query ObterSala($salaId: Int!) {
      sala(salaId: $salaId) {
        id
        nome
        local
        capacidade
        descricao
        criadorId
        ativa
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { salaId }, token);
}

export async function listarMinhasSalas(token, skip = 0, limit = 100) {
  const query = `
    query ListarMinhasSalas($skip: Int!, $limit: Int!) {
      minhasSalas(skip: $skip, limit: $limit) {
        id
        nome
        local
        capacidade
        descricao
        criadorId
        ativa
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { skip, limit }, token);
}

export async function criarSala(token, sala) {
  const query = `
    mutation CriarSala($sala: SalaInput!) {
      criarSala(sala: $sala) {
        id
        nome
        local
        capacidade
        descricao
        criadorId
        ativa
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { sala }, token);
}

export async function atualizarSala(token, salaId, sala) {
  const query = `
    mutation AtualizarSala($salaId: Int!, $sala: SalaUpdateInput!) {
      atualizarSala(salaId: $salaId, sala: $sala) {
        id
        nome
        local
        capacidade
        descricao
        criadorId
        ativa
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { salaId, sala }, token);
}

export async function deletarSala(token, salaId) {
  const query = `
    mutation DeletarSala($salaId: Int!) {
      deletarSala(salaId: $salaId)
    }
  `;
  
  return await graphqlRequest(query, { salaId }, token);
}

// Perfil
export async function obterMeuPerfil(token) {
  const query = `
    query ObterMeuPerfil {
      meuPerfil {
        id
        nome
        username
        email
        admin
        createdAt
      }
    }
  `;
  
  return await graphqlRequest(query, {}, token);
}

// Disponibilidade
export async function listarReservasPorSala(token, salaId, data) {
  const query = `
    query ListarReservasPorSala($salaId: Int!, $data: String!) {
      reservasPorSala(salaId: $salaId, data: $data) {
        id
        local
        sala
        salaId
        dataHoraInicio
        dataHoraFim
        responsavelId
        cafeQuantidade
        cafeDescricao
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { salaId, data }, token);
}

export async function obterHorariosDisponiveis(token, salaId, data, horaInicio = "08:00:00", horaFim = "18:00:00") {
  const query = `
    query ObterHorariosDisponiveis($salaId: Int!, $data: String!, $horaInicio: String, $horaFim: String) {
      horariosDisponiveis(salaId: $salaId, data: $data, horaInicio: $horaInicio, horaFim: $horaFim) {
        inicio
        fim
      }
    }
  `;
  
  return await graphqlRequest(query, { salaId, data, horaInicio, horaFim }, token);
}

export async function obterHorariosDisponiveisPorHora(token, salaId, data, horaInicio = "08:00:00", horaFim = "18:00:00") {
  const query = `
    query ObterHorariosDisponiveisPorHora($salaId: Int!, $data: String!, $horaInicio: String, $horaFim: String) {
      horariosDisponiveisPorHora(salaId: $salaId, data: $data, horaInicio: $horaInicio, horaFim: $horaFim)
    }
  `;
  
  return await graphqlRequest(query, { salaId, data, horaInicio, horaFim }, token);
}

export async function verificarDisponibilidade(token, salaId, dataHoraInicio, dataHoraFim) {
  const query = `
    query VerificarDisponibilidade($salaId: Int!, $dataHoraInicio: String!, $dataHoraFim: String!) {
      verificarDisponibilidade(salaId: $salaId, dataHoraInicio: $dataHoraInicio, dataHoraFim: $dataHoraFim)
    }
  `;
  
  return await graphqlRequest(query, { salaId, dataHoraInicio, dataHoraFim }, token);
}

export async function atualizarReserva(token, reservaId, reserva) {
  const query = `
    mutation AtualizarReserva($reservaId: Int!, $reserva: ReservaUpdateInput!) {
      atualizarReserva(reservaId: $reservaId, reserva: $reserva) {
        id
        local
        sala
        salaId
        dataHoraInicio
        dataHoraFim
        responsavelId
        cafeQuantidade
        cafeDescricao
        createdAt
        updatedAt
      }
    }
  `;
  
  return await graphqlRequest(query, { reservaId, reserva }, token);
}

export async function deletarReserva(token, reservaId) {
  const query = `
    mutation DeletarReserva($reservaId: Int!) {
      deletarReserva(reservaId: $reservaId)
    }
  `;
  
  return await graphqlRequest(query, { reservaId }, token);
}
```

---

## 7. Formato de Data/Hora

Todas as datas devem ser enviadas no formato **ISO 8601**:

```
YYYY-MM-DDTHH:mm:ss
```

**Exemplos:**
- `"2024-01-15T10:00:00"` - 15 de janeiro de 2024, 10:00:00
- `"2024-12-31T23:59:59"` - 31 de dezembro de 2024, 23:59:59

**JavaScript:**
```javascript
const dataHora = new Date().toISOString().slice(0, 19); // Remove os milissegundos
// Resultado: "2024-01-15T10:00:00"
```

---

## 8. Validações Importantes

1. **Conflito de Horário:** O sistema valida automaticamente se já existe uma reserva para a mesma sala no mesmo período
2. **Data de Fim > Data de Início:** A data/hora de fim deve ser sempre maior que a data/hora de início
3. **Permissões de Reserva:** Apenas o usuário que criou a reserva pode atualizá-la ou deletá-la
4. **Permissões de Sala:** Apenas **administradores** podem criar, atualizar ou deletar salas
5. **Usuário Admin:** Apenas usuários com `admin: true` podem gerenciar salas
6. **Senha:** Máximo de 72 caracteres
7. **Username e Email:** Devem ser únicos no sistema
8. **Sala Ativa:** Apenas salas ativas devem ser consideradas para reservas (use o filtro `apenasAtivas: true`)

### 8.1. Criar Usuário Administrador

Para criar um usuário administrador, use o script Python:

```bash
# Dentro do container Docker
docker compose exec api python create_admin.py admin admin@example.com senha123

# Ou localmente (se estiver rodando sem Docker)
python create_admin.py admin admin@example.com senha123
```

**Importante:** 
- O primeiro usuário admin deve ser criado manualmente usando o script
- Usuários criados via GraphQL (`criarUsuario`) **não** são administradores por padrão
- Apenas administradores podem criar, editar e deletar salas

---

## 9. Casos de Uso e Fluxos Completos

### 9.1. Fluxo Completo: Selecionar Sala e Reservar por Hora

**Este é o fluxo principal para reservar uma sala:**

**Passo 1: Listar salas disponíveis**
```graphql
query {
  salas(apenasAtivas: true) {
    id
    nome
    local
    capacidade
  }
}
```

**Passo 2: Selecionar uma sala e data, então buscar horários disponíveis por hora**
```graphql
query {
  horariosDisponiveisPorHora(
    salaId: 1
    data: "2024-01-20"
  )
}
```

**Resposta:** `["08:00", "09:00", "10:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]`

**Passo 3: Usuário seleciona uma hora (ex: "14:00") e cria reserva de 1 hora**
```graphql
mutation {
  criarReserva(reserva: {
    salaId: 1
    dataHoraInicio: "2024-01-20T14:00:00"
    dataHoraFim: "2024-01-20T15:00:00"
  }) {
    id
    salaId
    dataHoraInicio
    dataHoraFim
  }
}
```

**Nota:** Cada reserva é de 1 hora. Se o usuário selecionar "14:00", a reserva será das 14:00 às 15:00.

---

### 9.2. Fluxo Alternativo: Criar Sala e Fazer Reserva

**Passo 1: Criar uma sala**
```graphql
mutation {
  criarSala(sala: {
    nome: "Sala de Reuniões Executiva"
    local: "Edifício A - 3º Andar"
    capacidade: 20
    descricao: "Sala com projetor, quadro branco e sistema de videoconferência"
  }) {
    id
    nome
    local
    capacidade
  }
}
```

**Passo 2: Verificar horários disponíveis**
```graphql
query {
  horariosDisponiveis(
    salaId: 1
    data: "2024-01-20"
    horaInicio: "08:00:00"
    horaFim: "18:00:00"
  ) {
    inicio
    fim
  }
}
```

**Passo 3: Verificar disponibilidade de um horário específico**
```graphql
query {
  verificarDisponibilidade(
    salaId: 1
    dataHoraInicio: "2024-01-20T14:00:00"
    dataHoraFim: "2024-01-20T16:00:00"
  )
}
```

**Passo 4: Criar a reserva**
```graphql
mutation {
  criarReserva(reserva: {
    salaId: 1
    dataHoraInicio: "2024-01-20T14:00:00"
    dataHoraFim: "2024-01-20T16:00:00"
    cafeQuantidade: 10
    cafeDescricao: "Café expresso e água"
  }) {
    id
    salaId
    dataHoraInicio
    dataHoraFim
  }
}
```

### 9.3. Verificar se Usuário é Admin

**Verificar perfil do usuário:**
```graphql
query {
  meuPerfil {
    id
    nome
    username
    email
    admin
  }
}
```

**Exemplo de uso no frontend:**
```javascript
async function verificarSeAdmin(token) {
  try {
    const perfil = await obterMeuPerfil(token);
    return perfil.meuPerfil.admin;
  } catch (error) {
    console.error('Erro ao verificar perfil:', error);
    return false;
  }
}

// Usar no componente
const [isAdmin, setIsAdmin] = useState(false);

useEffect(() => {
  async function checkAdmin() {
    const token = localStorage.getItem('token');
    if (token) {
      const admin = await verificarSeAdmin(token);
      setIsAdmin(admin);
    }
  }
  checkAdmin();
}, []);
```

---

### 9.4. Consultar Agenda de uma Sala

**Ver todas as reservas de uma sala em um dia:**
```graphql
query {
  reservasPorSala(salaId: 1, data: "2024-01-20") {
    id
    dataHoraInicio
    dataHoraFim
    responsavelId
    cafeQuantidade
  }
}
```

**Ver horários disponíveis:**
```graphql
query {
  horariosDisponiveis(salaId: 1, data: "2024-01-20") {
    inicio
    fim
  }
}
```

### 9.6. Gerenciar Minhas Salas (Apenas Admin)

**Listar minhas salas:**
```graphql
query {
  minhasSalas {
    id
    nome
    local
    ativa
    createdAt
  }
}
```

**Desativar uma sala:**
```graphql
mutation {
  atualizarSala(
    salaId: 1
    sala: {
      ativa: false
    }
  ) {
    id
    nome
    ativa
  }
}
```

### 9.4. Exemplo Prático: Componente React para Seleção de Sala e Horário

**Fluxo:** Usuário seleciona uma sala → Sistema mostra apenas as horas disponíveis → Usuário seleciona uma hora → Sistema cria reserva de 1 hora

```javascript
import { useState, useEffect } from 'react';
import { 
  listarSalas, 
  obterHorariosDisponiveisPorHora, 
  criarReserva 
} from './api';

function ReservarSala() {
  const [salas, setSalas] = useState([]);
  const [salaSelecionada, setSalaSelecionada] = useState(null);
  const [data, setData] = useState('');
  const [horasDisponiveis, setHorasDisponiveis] = useState([]);
  const [horaSelecionada, setHoraSelecionada] = useState(null);
  const [loading, setLoading] = useState(false);

  // Carrega salas ao montar o componente
  useEffect(() => {
    async function carregarSalas() {
      try {
        const token = localStorage.getItem('token');
        const resultado = await listarSalas(token, 0, 100, true); // Apenas salas ativas
        setSalas(resultado.salas);
      } catch (error) {
        console.error('Erro ao carregar salas:', error);
      }
    }
    carregarSalas();
  }, []);

  // Carrega horários disponíveis quando sala e data são selecionados
  useEffect(() => {
    if (salaSelecionada && data) {
      carregarHorariosDisponiveis();
    } else {
      setHorasDisponiveis([]);
    }
  }, [salaSelecionada, data]);

  async function carregarHorariosDisponiveis() {
    if (!salaSelecionada || !data) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const resultado = await obterHorariosDisponiveisPorHora(
        token,
        salaSelecionada.id,
        data,
        "08:00:00",
        "18:00:00"
      );
      setHorasDisponiveis(resultado.horariosDisponiveisPorHora || []);
    } catch (error) {
      console.error('Erro ao carregar horários:', error);
      setHorasDisponiveis([]);
    } finally {
      setLoading(false);
    }
  }

  const handleReservar = async () => {
    if (!salaSelecionada || !data || !horaSelecionada) {
      alert('Selecione uma sala, data e horário');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      
      // Cria data/hora de início e fim (slot de 1 hora)
      const dataHoraInicio = `${data}T${horaSelecionada}:00`;
      const [hora, minuto] = horaSelecionada.split(':');
      const horaFim = String(parseInt(hora) + 1).padStart(2, '0');
      const dataHoraFim = `${data}T${horaFim}:${minuto}:00`;
      
      await criarReserva(token, {
        salaId: salaSelecionada.id,
        dataHoraInicio: dataHoraInicio,
        dataHoraFim: dataHoraFim
      });
      
      alert('Reserva criada com sucesso!');
      
      // Limpar seleções e recarregar horários
      setHoraSelecionada(null);
      carregarHorariosDisponiveis();
    } catch (error) {
      alert('Erro ao criar reserva: ' + error.message);
    }
  };

  // Formata data para input type="date"
  const hoje = new Date().toISOString().split('T')[0];

  return (
    <div className="reservar-sala">
      <h2>Reservar Sala</h2>
      
      {/* Seleção de Sala */}
      <div className="form-group">
        <label>Selecione a Sala:</label>
        <select 
          value={salaSelecionada?.id || ''} 
          onChange={(e) => {
            const sala = salas.find(s => s.id === parseInt(e.target.value));
            setSalaSelecionada(sala);
            setHoraSelecionada(null);
          }}
        >
          <option value="">-- Selecione uma sala --</option>
          {salas.map(sala => (
            <option key={sala.id} value={sala.id}>
              {sala.nome} - {sala.local} {sala.capacidade && `(${sala.capacidade} pessoas)`}
            </option>
          ))}
        </select>
      </div>

      {/* Seleção de Data */}
      <div className="form-group">
        <label>Selecione a Data:</label>
        <input
          type="date"
          value={data}
          min={hoje}
          onChange={(e) => {
            setData(e.target.value);
            setHoraSelecionada(null);
          }}
        />
      </div>

      {/* Horários Disponíveis */}
      {salaSelecionada && data && (
        <div className="horarios-disponiveis">
          <h3>Horários Disponíveis</h3>
          {loading ? (
            <p>Carregando horários...</p>
          ) : horasDisponiveis.length === 0 ? (
            <p className="sem-horarios">
              Não há horários disponíveis para esta sala nesta data.
            </p>
          ) : (
            <>
              <div className="grid-horarios">
                {horasDisponiveis.map((hora, index) => {
                  const horaFim = `${String(parseInt(hora.split(':')[0]) + 1).padStart(2, '0')}:00`;
                  return (
                    <button
                      key={index}
                      onClick={() => setHoraSelecionada(hora)}
                      className={`hora-slot ${horaSelecionada === hora ? 'selected' : ''}`}
                    >
                      {hora} - {horaFim}
                    </button>
                  );
                })}
              </div>
              
              {horaSelecionada && (
                <div className="confirmacao">
                  <p>
                    Reservar <strong>{salaSelecionada.nome}</strong> em{' '}
                    <strong>{new Date(data).toLocaleDateString('pt-BR')}</strong> das{' '}
                    <strong>{horaSelecionada}</strong> às{' '}
                    <strong>{String(parseInt(horaSelecionada.split(':')[0]) + 1).padStart(2, '0')}:00</strong>?
                  </p>
                  <button onClick={handleReservar} className="btn-reservar">
                    Confirmar Reserva
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default ReservarSala;
```

**CSS de exemplo:**
```css
.reservar-sala {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group select,
.form-group input[type="date"] {
  width: 100%;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.horarios-disponiveis {
  margin-top: 30px;
}

.grid-horarios {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  margin-top: 15px;
}

.hora-slot {
  padding: 15px;
  border: 2px solid #ddd;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.hora-slot:hover {
  border-color: #4CAF50;
  background: #f0f8f0;
}

.hora-slot.selected {
  border-color: #4CAF50;
  background: #4CAF50;
  color: white;
  font-weight: bold;
}

.sem-horarios {
  padding: 20px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  color: #856404;
}

.confirmacao {
  margin-top: 20px;
  padding: 20px;
  background: #e7f3ff;
  border: 1px solid #2196F3;
  border-radius: 8px;
}

.btn-reservar {
  margin-top: 15px;
  padding: 12px 30px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  font-weight: bold;
}

.btn-reservar:hover {
  background: #45a049;
}
```

### 9.6. Exemplo: Calendário de Disponibilidade

```javascript
async function obterCalendarioDisponibilidade(salaId, mes, ano) {
  const token = localStorage.getItem('token');
  const diasNoMes = new Date(ano, mes, 0).getDate();
  const calendario = [];

  for (let dia = 1; dia <= diasNoMes; dia++) {
    const data = `${ano}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
    
    try {
      const horarios = await obterHorariosDisponiveis(token, salaId, data);
      const disponivel = horarios.horariosDisponiveis.length > 0;
      
      calendario.push({
        data,
        disponivel,
        horariosDisponiveis: horarios.horariosDisponiveis
      });
    } catch (error) {
      console.error(`Erro ao obter disponibilidade para ${data}:`, error);
    }
  }

  return calendario;
}
```

---

## 10. Boas Práticas e Dicas

### 10.1. Gerenciamento de Token

- **Armazenar token:** Use `localStorage` ou `sessionStorage` para persistir o token
- **Renovação:** O token expira em 30 minutos (padrão). Implemente renovação automática ou redirecione para login
- **Validação:** Sempre verifique se o token existe antes de fazer requisições autenticadas

```javascript
// Exemplo de verificação de token
function getToken() {
  const token = localStorage.getItem('token');
  if (!token) {
    // Redirecionar para login
    window.location.href = '/login';
    return null;
  }
  return token;
}
```

### 10.2. Tratamento de Erros

- **Sempre trate erros:** Use try/catch em todas as chamadas à API
- **Mensagens amigáveis:** Traduza mensagens de erro para o usuário
- **Logs:** Mantenha logs de erros para debug (mas não exponha informações sensíveis)

```javascript
async function fazerRequisicao(query, variables, token) {
  try {
    const response = await fetch('http://localhost:8000/graphql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ query, variables })
    });

    const data = await response.json();
    
    if (data.errors) {
      // Tratar erros GraphQL
      const mensagem = data.errors[0].message;
      if (mensagem.includes('Token')) {
        // Token inválido - redirecionar para login
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      throw new Error(mensagem);
    }
    
    return data.data;
  } catch (error) {
    console.error('Erro na requisição:', error);
    throw error;
  }
}
```

### 10.3. Cache e Performance

- **Cache de salas:** Cache a lista de salas para evitar requisições desnecessárias
- **Debounce:** Use debounce ao buscar horários disponíveis enquanto o usuário digita/seleciona
- **Paginação:** Use paginação para listas grandes (skip/limit)

```javascript
// Exemplo de cache simples
const cacheSalas = {
  data: null,
  timestamp: null,
  TTL: 5 * 60 * 1000 // 5 minutos
};

async function getSalasComCache(token) {
  const agora = Date.now();
  
  if (cacheSalas.data && cacheSalas.timestamp && 
      (agora - cacheSalas.timestamp) < cacheSalas.TTL) {
    return cacheSalas.data;
  }
  
  const salas = await listarSalas(token);
  cacheSalas.data = salas;
  cacheSalas.timestamp = agora;
  
  return salas;
}
```

### 10.4. Validação no Frontend

- **Valide antes de enviar:** Verifique se os dados estão corretos antes de fazer a requisição
- **Formato de data:** Sempre use o formato ISO 8601 para datas
- **Horários:** Valide que o horário de fim é maior que o de início

```javascript
function validarReserva(reserva) {
  const erros = [];
  
  if (!reserva.salaId && !reserva.sala) {
    erros.push('É necessário informar uma sala');
  }
  
  if (!reserva.dataHoraInicio || !reserva.dataHoraFim) {
    erros.push('É necessário informar horário de início e fim');
  }
  
  if (reserva.dataHoraInicio && reserva.dataHoraFim) {
    const inicio = new Date(reserva.dataHoraInicio);
    const fim = new Date(reserva.dataHoraFim);
    
    if (fim <= inicio) {
      erros.push('O horário de fim deve ser maior que o horário de início');
    }
  }
  
  return erros;
}
```

### 10.5. UX Recomendada

1. **Feedback visual:** Mostre loading states durante requisições
2. **Confirmação:** Peça confirmação antes de deletar reservas/salas
3. **Atualização:** Recarregue dados após criar/atualizar/deletar
4. **Horários disponíveis:** Mostre horários disponíveis antes de permitir reserva
5. **Validação em tempo real:** Verifique disponibilidade antes de submeter o formulário
6. **Controle de acesso:** Verifique se o usuário é admin antes de mostrar opções de criar/editar/deletar salas
7. **Mensagens claras:** Informe ao usuário quando ele não tem permissão para realizar uma ação

### 10.6. Estrutura de Pastas Recomendada

```
src/
├── api/
│   ├── graphql.js          # Funções de requisição GraphQL
│   ├── auth.js             # Funções de autenticação
│   └── queries.js          # Queries GraphQL
├── components/
│   ├── Salas/
│   │   ├── ListaSalas.js
│   │   ├── CriarSala.js
│   │   └── EditarSala.js
│   └── Reservas/
│       ├── ListaReservas.js
│       ├── CriarReserva.js
│       └── SelecionarHorario.js
├── hooks/
│   ├── useAuth.js          # Hook para autenticação
│   └── useSalas.js         # Hook para gerenciar salas
└── utils/
    ├── formatDate.js       # Formatação de datas
    └── validators.js       # Validadores
```

---

## 11. Testando no GraphiQL

Acesse `http://localhost:8000/graphql` no navegador para usar o GraphiQL interativo.

Para adicionar o header de autenticação no GraphiQL:
1. Clique no ícone de engrenagem (⚙️) ou na aba "Headers"
2. Adicione:
```json
{
  "Authorization": "Bearer seu_token_aqui"
}
```

### 11.1. Exemplo de Teste Completo no GraphiQL

**1. Criar usuário:**
```graphql
mutation {
  criarUsuario(usuario: {
    username: "teste"
    email: "teste@example.com"
    password: "senha123"
  }) {
    id
    username
  }
}
```

**2. Fazer login:**
```graphql
mutation {
  login(loginData: {
    username: "teste"
    password: "senha123"
  }) {
    accessToken
  }
}
```

**3. Criar sala (com token no header):**
```graphql
mutation {
  criarSala(sala: {
    nome: "Sala Teste"
    local: "Edifício Teste"
    capacidade: 10
  }) {
    id
    nome
  }
}
```

**4. Ver horários disponíveis:**
```graphql
query {
  horariosDisponiveis(salaId: 1, data: "2024-01-20") {
    inicio
    fim
  }
}
```

**5. Criar reserva:**
```graphql
mutation {
  criarReserva(reserva: {
    salaId: 1
    dataHoraInicio: "2024-01-20T10:00:00"
    dataHoraFim: "2024-01-20T12:00:00"
  }) {
    id
    salaId
    dataHoraInicio
    dataHoraFim
  }
}
```

