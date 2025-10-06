# ReportMe Frontend Documentation

## Tecnologias Utilizadas

- **React 18** com TypeScript
- **Material-UI (MUI)** para componentes de interface
- **React Router DOM** para roteamento
- **Axios** para requisições HTTP
- **Context API** para gerenciamento de estado

## Estrutura do Projeto

```
src/
├── components/        # Componentes reutilizáveis
│   └── ProtectedRoute.tsx
├── contexts/         # Contextos React (gerenciamento de estado)
│   └── AuthContext.tsx
├── pages/           # Páginas da aplicação
│   ├── LoginPage.tsx
│   └── DashboardPage.tsx
├── services/        # Serviços de API
│   └── api.ts
├── types/          # Tipos TypeScript
│   └── index.ts
├── utils/          # Utilitários
├── App.tsx         # Componente principal
└── index.tsx       # Entry point
```

## Configuração de Ambiente

### Variáveis de Ambiente (.env)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
```

### Scripts Disponíveis
```bash
npm start          # Inicia servidor de desenvolvimento
npm run build      # Build para produção
npm test           # Executa testes
npm run eject      # Ejeta configurações do CRA
```

## Funcionalidades Implementadas

### ✅ Autenticação
- Login com JWT
- Context API para gerenciamento de estado de autenticação
- Interceptors Axios para refresh token automático
- Rotas protegidas

### ✅ Páginas
- **LoginPage**: Tela de login com Material-UI
- **DashboardPage**: Dashboard inicial com informações do usuário

### ✅ Componentes
- **ProtectedRoute**: Componente para proteger rotas autenticadas
- **AuthContext**: Context para gerenciamento de autenticação

### ✅ Serviços
- **authService**: Serviços de autenticação (login, logout, perfil)
- **coreService**: Serviços do core da aplicação (health check)

## Tipos TypeScript

### Principais interfaces definidas:
- `User`: Dados do usuário
- `AuthState`: Estado de autenticação
- `Connection`: Conexões de banco de dados
- `Query`: Consultas SQL
- `Project`: Projetos e nós hierárquicos
- `Parameter`: Parâmetros de consultas

## Como Testar

1. **Iniciar Backend**:
```bash
cd reportme_api
source ../report_me/bin/activate
python manage.py runserver
```

2. **Iniciar Frontend**:
```bash
cd reportme_front
npm start
```

3. **Acessar aplicação**: http://localhost:3000

### Usuário de Teste
- **Usuário**: admin
- **Senha**: Teste@123

## Status das Funcionalidades

### ✅ Funcionando
- Autenticação JWT
- Login/Logout
- Dashboard básico
- Roteamento protegido
- Conexão com API Django

### 🚧 Em Desenvolvimento (próximas fases)
- CRUD de Projetos
- CRUD de Conexões
- Editor de Consultas
- Visualização em árvore
- Execução de relatórios
- Exportação para Excel

## Próximos Passos

1. **Fase 2**: Implementar modelos Django no backend
2. **Fase 3**: Criar APIs CRUD completas
3. **Fase 4**: Implementar interfaces de administração
4. **Fase 5**: Portal de relatórios para usuários finais
