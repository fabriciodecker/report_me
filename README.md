# ReportMe - Portal de Relatórios

Portal de relatórios corporativo desenvolvido com Django REST Framework e React.

## Estrutura do Projeto

- **reportme_api/**: Backend API Django REST Framework
- **reportme_front/**: Frontend React com TypeScript
- **docs/**: Documentação do projeto

## Tecnologias

### Backend
- Python 3.x
- Django REST Framework
- JWT Authentication
- SQLite (desenvolvimento) / PostgreSQL (produção)
- Suporte a PostgreSQL, SQL Server, Oracle

### Frontend
- React 18
- TypeScript
- Material-UI
- Axios

## Desenvolvimento

### Pré-requisitos
- Docker e Docker Compose
- OU Python 3.8+ e Node.js 16+ (para desenvolvimento local)

### 🐳 Desenvolvimento com Docker (Recomendado)

1. **Clonar o repositório**:
```bash
git clone <repo-url>
cd report_me
```

2. **Iniciar ambiente de desenvolvimento**:
```bash
./dev.sh start
```

3. **Acessar aplicação**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin Django: http://localhost:8000/admin

4. **Comandos úteis**:
```bash
./dev.sh logs           # Ver logs
./dev.sh shell-api      # Shell Django
./dev.sh migrate        # Executar migrações
./dev.sh superuser      # Criar superusuário
./dev.sh stop           # Parar ambiente
```

### 🔧 Desenvolvimento Local (Sem Docker)

1. **Backend**:
```bash
cd reportme_api
python -m venv ../report_me
source ../report_me/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

2. **Frontend**:
```bash
cd reportme_front
npm install
npm start
```

### 👤 Usuário de Teste
- **Usuário**: admin
- **Senha**: Teste@123

## Funcionalidades

- Autenticação e autorização por níveis (Admin, Editor, Leitor)
- Gerenciamento de conexões com diferentes SGBDs
- Criação e organização hierárquica de projetos
- Editor de consultas SQL com parâmetros
- Execução de consultas e visualização de resultados
- Exportação de dados para Excel
- Interface administrativa completa
- Portal de relatórios para usuários finais

## Status do Projeto

🚧 **Em desenvolvimento** - Veja o [Plano de Execução](execution_plan.md) para detalhes.

## Licença

[Definir licença]
