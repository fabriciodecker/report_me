# ReportMe API - Documentação

## 📋 Visão Geral

O **ReportMe** é uma API REST completa para gerenciamento de relatórios corporativos, desenvolvida em Django REST Framework. A API permite criar projetos hierárquicos, configurar conexões com bancos de dados, desenvolver consultas SQL parametrizadas e executar relatórios dinâmicos.

## 🚀 Acesso à Documentação

### URLs da Documentação

| Interface | URL | Descrição |
|-----------|-----|-----------|
| **Swagger UI** | http://localhost:8000/api/docs/ | Interface interativa para testar a API |
| **ReDoc** | http://localhost:8000/api/redoc/ | Documentação estática elegante |
| **Schema OpenAPI** | http://localhost:8000/api/schema/ | Schema JSON/YAML da API |

### Como Acessar

1. **Iniciar o servidor:**
   ```bash
   python manage.py runserver
   ```

2. **Acessar no navegador:**
   - Swagger UI: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/

## 🔐 Autenticação

A API utiliza **autenticação JWT (JSON Web Tokens)**. Para acessar endpoints protegidos:

### 1. Obter Token de Acesso

**Endpoint:** `POST /api/auth/login/`

```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "seu_usuario",
    "email": "email@exemplo.com"
  }
}
```

### 2. Usar Token nas Requisições

Adicione o token no header `Authorization`:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 3. Na Documentação Swagger

1. Clique no botão **"Authorize"** 🔒 no topo da página
2. Digite: `Bearer SEU_TOKEN_AQUI`
3. Clique em **"Authorize"**

## 📊 Principais Funcionalidades

### 🗂️ **Projetos** (`/api/core/projects/`)
- **Listagem** com busca e filtros
- **Criação** de projetos hierárquicos
- **Estrutura em árvore** para organização
- **Permissões** granulares por usuário

### 🌳 **Nós de Projeto** (`/api/core/project-nodes/`)
- **Hierarquia** de pastas e relatórios
- **Associação** com consultas SQL
- **Navegação** intuitiva tipo árvore
- **Metadados** customizáveis

### 🔗 **Conexões** (`/api/core/connections/`)
- **Múltiplos SGBDs:** PostgreSQL, MySQL, SQLite, SQL Server, Oracle
- **Teste de conectividade** antes de salvar
- **Credenciais seguras** com criptografia
- **Pool de conexões** otimizado

### 📋 **Consultas SQL** (`/api/core/queries/`)
- **Editor SQL** com validação de sintaxe
- **Parâmetros tipados** (string, number, date, boolean, list)
- **Execução segura** com timeout configurável
- **Histórico** de execuções

### ⚡ **Execução** (`/api/core/execute-query/`)
- **Parâmetros dinâmicos** via interface
- **Resultados paginados** 
- **Exportação** CSV/Excel
- **Cache** configurável

## 🔍 Exemplos Práticos

### Criar um Projeto

```bash
curl -X POST "http://localhost:8000/api/core/projects/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Relatórios de Vendas",
    "description": "Projeto para relatórios do setor comercial",
    "is_public": false
  }'
```

### Configurar Conexão PostgreSQL

```bash
curl -X POST "http://localhost:8000/api/core/connections/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Base de Vendas",
    "sgbd": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "vendas_db",
    "user": "vendas_user",
    "password": "senha_secreta"
  }'
```

### Criar Consulta com Parâmetros

```bash
curl -X POST "http://localhost:8000/api/core/queries/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vendas por Período",
    "query": "SELECT * FROM vendas WHERE data_venda BETWEEN :data_inicio AND :data_fim AND valor >= :valor_minimo",
    "connection": 1,
    "query_parameters": [
      {
        "name": "data_inicio",
        "type": "date",
        "allow_null": false,
        "default_value": "2024-01-01"
      },
      {
        "name": "data_fim", 
        "type": "date",
        "allow_null": false,
        "default_value": "2024-12-31"
      },
      {
        "name": "valor_minimo",
        "type": "number",
        "allow_null": true,
        "default_value": "100"
      }
    ]
  }'
```

### Executar Consulta

```bash
curl -X POST "http://localhost:8000/api/core/execute-query/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM vendas WHERE data_venda BETWEEN :data_inicio AND :data_fim",
    "connection_id": 1,
    "parameters": {
      "data_inicio": "2024-01-01",
      "data_fim": "2024-03-31"
    }
  }'
```

## 📋 Recursos de Teste

### Testar Conexão

```bash
curl -X POST "http://localhost:8000/api/core/test-connection/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sgbd": "postgresql",
    "host": "localhost", 
    "port": 5432,
    "database": "test_db",
    "user": "test_user",
    "password": "test_password"
  }'
```

## 🏷️ Tags da API

| Tag | Descrição | Endpoints |
|-----|-----------|-----------|
| **authentication** | Login, registro, recuperação de senha | `/api/auth/*` |
| **projects** | Gerenciamento de projetos | `/api/core/projects/*` |
| **project-nodes** | Estrutura hierárquica | `/api/core/project-nodes/*` |
| **connections** | Conexões com bancos | `/api/core/connections/*` |
| **queries** | Consultas SQL | `/api/core/queries/*` |
| **system** | Health check e status | `/api/core/health/*` |

## 🔧 Configuração Local

### Pré-requisitos

```bash
# Python 3.8+
pip install -r requirements.txt

# Banco de dados (PostgreSQL recomendado)
# SQLite (desenvolvimento) já incluído
```

### Variáveis de Ambiente

```env
DEBUG=True
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgresql://user:pass@localhost:5432/reportme
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Inicialização

```bash
# Migrações
python manage.py migrate

# Superusuário
python manage.py createsuperuser

# Servidor de desenvolvimento
python manage.py runserver
```

## 📚 Recursos Adicionais

- **Admin Django:** http://localhost:8000/admin/
- **Teste Interativo:** Use o Swagger UI para explorar endpoints
- **Validação de Schema:** Suporte completo OpenAPI 3.0
- **Autenticação JWT:** Tokens com refresh automático
- **Paginação:** Padrão em todas as listagens
- **Filtros:** Busca e ordenação avançadas

---

## 💡 Dicas de Uso

1. **Sempre use HTTPS** em produção
2. **Configure timeouts** adequados para consultas longas  
3. **Use cache** para consultas frequentes
4. **Monitore logs** de execução de queries
5. **Teste conexões** antes de criar consultas
6. **Use parâmetros** para consultas dinâmicas
7. **Implemente** rate limiting em produção

---

**Desenvolvido com ❤️ usando Django REST Framework**