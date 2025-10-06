# 📚 Documentação da API ReportMe - Swagger/OpenAPI

## 🚀 Como Acessar

A documentação interativa da API está disponível em:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema OpenAPI**: http://localhost:8000/api/schema/

## 🔐 Autenticação

### 1. Login
Para testar os endpoints autenticados, primeiro faça login:

**Endpoint**: `POST /api/auth/login/`

**Credenciais de Teste**:
```json
{
  "username": "admin",
  "password": "Teste@123"
}
```

**Resposta**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@reportme.com",
    "user_type": "admin"
  }
}
```

### 2. Autenticação no Swagger (PROCESSO CORRETO)

⚠️ **IMPORTANTE**: O botão "Authorize" NÃO faz login automático! Você precisa primeiro obter o token.

**Processo passo a passo:**

1. **Faça login no próprio Swagger:**
   - Vá até a seção "authentication" 
   - Clique em `POST /api/auth/login/`
   - Clique em "Try it out"
   - Insira as credenciais e clique "Execute"

2. **Copie o token `access` da resposta**

3. **Configure a autorização:**
   - Clique no botão **"Authorize"** no topo da página
   - No campo "Value", digite: `Bearer SEU_TOKEN_AQUI`
   - Exemplo: `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`
   - Clique em "Authorize"

4. **Agora você pode testar todos os endpoints autenticados!**

🔒 **O ícone de cadeado** ao lado dos endpoints indica que eles requerem autenticação.

## 📋 Endpoints Disponíveis

### 🔐 Autenticação
- `POST /api/auth/login/` - Login do usuário
- `POST /api/auth/register/` - Registro de novo usuário
- `POST /api/auth/refresh/` - Renovar token
- `GET /api/auth/profile/` - Perfil do usuário

### 📁 Projetos
- `GET /api/core/projects/` - Listar projetos
- `POST /api/core/projects/` - Criar projeto
- `GET /api/core/projects/{id}/` - Obter projeto
- `PUT /api/core/projects/{id}/` - Atualizar projeto
- `DELETE /api/core/projects/{id}/` - Excluir projeto
- `GET /api/core/projects/{id}/tree/` - Árvore do projeto
- `POST /api/core/projects/{id}/duplicate/` - Duplicar projeto

### 🔗 Conexões
- `GET /api/core/connections/` - Listar conexões
- `POST /api/core/connections/` - Criar conexão
- `GET /api/core/connections/{id}/` - Obter conexão
- `PUT /api/core/connections/{id}/` - Atualizar conexão
- `DELETE /api/core/connections/{id}/` - Excluir conexão
- `POST /api/core/connections/test-connection/` - Testar conexão
- `POST /api/core/connections/{id}/duplicate/` - Duplicar conexão

### 🌳 Nós de Projeto
- `GET /api/core/project-nodes/` - Listar nós
- `POST /api/core/project-nodes/` - Criar nó
- `GET /api/core/project-nodes/{id}/` - Obter nó
- `PUT /api/core/project-nodes/{id}/` - Atualizar nó
- `DELETE /api/core/project-nodes/{id}/` - Excluir nó
- `POST /api/core/project-nodes/{id}/move/` - Mover nó
- `POST /api/core/project-nodes/{id}/duplicate/` - Duplicar nó

### ⚡ Sistema
- `GET /api/core/health/` - Health Check

## 🧪 Exemplos de Teste

### Criar um Projeto
```json
{
  "name": "Relatórios Financeiros",
  "description": "Projeto para relatórios do departamento financeiro"
}
```

### Criar uma Conexão PostgreSQL
```json
{
  "name": "BD Produção",
  "sgbd": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "reportme_prod",
  "user": "postgres",
  "password": "senha123"
}
```

### Testar Conexão Temporária
```json
{
  "sgbd": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "test_db",
  "user": "postgres",
  "password": "senha123"
}
```

### Testar Conexão Existente
```json
{
  "connection_id": 1
}
```

## 📋 Tipos de Banco Suportados

- `postgresql` - PostgreSQL
- `mysql` - MySQL/MariaDB
- `sqlserver` - Microsoft SQL Server
- `oracle` - Oracle Database
- `sqlite` - SQLite

## 🛡️ Níveis de Permissão

- **admin** - Acesso total ao sistema
- **manager** - Gerenciar projetos e usuários
- **editor** - Criar e editar projetos
- **viewer** - Apenas visualização

## 💡 Dicas

1. **Use o botão "Try it out"** em cada endpoint para testar diretamente no Swagger
2. **Veja os exemplos** disponíveis em cada endpoint
3. **Confira os códigos de resposta** para entender os resultados
4. **Use filtros e paginação** nos endpoints de listagem
5. **Teste diferentes cenários** de erro para entender as validações

## 🔧 Desenvolvimento

Para adicionar novos endpoints à documentação:

1. Use os decorators `@extend_schema` e `@extend_schema_view`
2. Adicione tags apropriadas para organização
3. Inclua exemplos claros nos decorators
4. Documente parâmetros e respostas

O schema é gerado automaticamente baseado nos serializers e views do Django REST Framework.
