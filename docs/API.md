# ReportMe API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
A API usa JWT (JSON Web Token) para autenticação.

### Endpoints de Autenticação

#### 1. Login (Customizado com informações do usuário)
```
POST /api/auth/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "Teste@123"
}
```

**Resposta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@reportme.com",
        "name": "",
        "full_name": "admin",
        "is_staff": true,
        "is_admin": false,
        "user_type": "Super Administrador"
    }
}
```

#### 2. Refresh Token
```
POST /api/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 3. Registro de Usuário
```
POST /api/auth/register/
Content-Type: application/json

{
    "username": "novousuario",
    "email": "novo@reportme.com",
    "name": "Nome Completo",
    "password": "Teste@123",
    "password_confirm": "Teste@123"
}
```

#### 4. Perfil do usuário
```
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@reportme.com",
    "name": "",
    "full_name": "admin",
    "first_name": "",
    "last_name": "",
    "is_staff": true,
    "is_admin": false,
    "user_type": "Super Administrador",
    "preferences": {},
    "created_at": "2025-10-02T15:14:00.539100-03:00",
    "updated_at": "2025-10-02T15:14:00.539139-03:00"
}
```

#### 5. Atualizar Perfil
```
PUT /api/auth/profile/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Nome Atualizado",
    "email": "novo@email.com"
}
```

#### 6. Alterar Senha
```
POST /api/auth/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "old_password": "senhaAtual",
    "new_password": "novaSenha@123",
    "new_password_confirm": "novaSenha@123"
}
```

#### 7. Esqueci a Senha
```
POST /api/auth/forgot-password/
Content-Type: application/json

{
    "email": "usuario@reportme.com"
}
```

#### 8. Reset de Senha
```
POST /api/auth/reset-password/
Content-Type: application/json

{
    "token": "token_recebido_por_email",
    "new_password": "novaSenha@123",
    "new_password_confirm": "novaSenha@123"
}
```

#### 9. Listar Usuários (Admin only)
```
GET /api/auth/users/
Authorization: Bearer <access_token>
```

### Endpoints Core

#### 1. Health Check
```
GET /api/core/health/
```

**Resposta:**
```json
{
    "status": "healthy",
    "message": "ReportMe API is running",
    "version": "1.0.0",
    "timestamp": "2024-09-28"
}
```

## Tipos de Usuário

| Tipo | Descrição | Permissões |
|------|-----------|------------|
| Super Administrador | `is_superuser=True` | Acesso total ao sistema |
| Administrador | `is_admin=True` | Gerenciamento completo |
| Editor | `is_staff=True` | Criação e edição de conteúdo |
| Somente Leitura | Usuário padrão | Apenas visualização |

## Headers para requisições autenticadas
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Usuários de Teste

### Admin
- **Username:** admin
- **Email:** admin@reportme.com
- **Password:** Teste@123
- **Tipo:** Super Administrador

### Usuário Normal
- **Username:** testuser
- **Email:** test@reportme.com
- **Password:** Teste@123
- **Tipo:** Somente Leitura

## Status dos Endpoints

✅ **Funcionando:**
- Health Check
- Login JWT (customizado)
- Refresh Token
- Registro de usuários
- Perfil do usuário
- Atualização de perfil
- Alteração de senha
- Esqueci/Reset senha (básico)
- Listagem de usuários (admin)

🚧 **Em desenvolvimento:**
- CRUD de Projetos
- CRUD de Conexões
- CRUD de Consultas
- Execução de Consultas
- Sistema de permissões avançado
