# Docker Configuration - ReportMe

Este documento descreve a configuração Docker para o projeto ReportMe.

## Estrutura de Arquivos Docker

```
report_me/
├── docker-compose.yml         # Produção com PostgreSQL
├── docker-compose.dev.yml     # Desenvolvimento com SQLite
├── docker-compose.prod.yml    # Produção completa com Nginx
├── dev.sh                     # Script de desenvolvimento
├── reportme_api/
│   └── Dockerfile            # Backend Django
└── reportme_front/
    └── Dockerfile            # Frontend React
```

## Ambientes

### 🔧 Desenvolvimento Local
- **Arquivo**: `docker-compose.dev.yml`
- **Banco**: SQLite (arquivo local)
- **Ports**: API (8000), Frontend (3000)
- **Volume mounting**: Código montado para hot reload

```bash
./dev.sh start    # Iniciar ambiente
./dev.sh logs     # Ver logs
./dev.sh stop     # Parar ambiente
```

### 🚀 Produção
- **Arquivo**: `docker-compose.prod.yml`
- **Banco**: PostgreSQL em container
- **Proxy**: Nginx para SSL/Load Balancing
- **Persistência**: Volumes para dados

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Comandos do Script dev.sh

| Comando | Descrição |
|---------|-----------|
| `start` | Iniciar ambiente de desenvolvimento |
| `stop` | Parar todos os containers |
| `restart` | Reiniciar ambiente |
| `logs` | Visualizar logs em tempo real |
| `shell-api` | Shell Django (manage.py shell) |
| `shell-backend` | Shell do container backend |
| `shell-frontend` | Shell do container frontend |
| `migrate` | Executar migrações do Django |
| `makemigrations` | Criar migrações |
| `superuser` | Criar superusuário |
| `test-api` | Executar testes da API |
| `test-frontend` | Executar testes do frontend |
| `clean` | Limpar containers e volumes |
| `build` | Construir imagens do zero |

## Configuração de Ambiente

### Desenvolvimento
```bash
cp .env.example .env
# Editar .env conforme necessário
```

### Produção
```bash
# Configurar variáveis no arquivo .env
SECRET_KEY=your-production-secret-key
DB_PASSWORD=secure-password
ALLOWED_HOSTS=yourdomain.com
REACT_APP_API_URL=https://yourdomain.com/api
```

## Volumes

### Desenvolvimento
- `./reportme_api:/app` - Hot reload do backend
- `./reportme_front:/app` - Hot reload do frontend
- `/app/node_modules` - Cache de node_modules

### Produção
- `postgres_data` - Dados do PostgreSQL
- `static_files` - Arquivos estáticos Django
- `media_files` - Uploads de arquivos

## Networks

- **reportme_network**: Rede bridge para comunicação entre containers

## Portas Expostas

### Desenvolvimento
- **3000**: Frontend React
- **8000**: Backend Django
- **5432**: PostgreSQL (se usado)

### Produção
- **80**: Nginx (HTTP)
- **443**: Nginx (HTTPS)
- **5432**: PostgreSQL

## Troubleshooting

### Container não inicia
```bash
./dev.sh logs    # Ver logs de erro
./dev.sh clean   # Limpar e tentar novamente
./dev.sh build   # Reconstruir imagens
```

### Problemas de permissão
```bash
sudo chown -R $USER:$USER .
```

### Reset completo
```bash
./dev.sh stop
./dev.sh clean
docker system prune -a
./dev.sh build
./dev.sh start
```

## Performance

### Desenvolvimento
- Hot reload habilitado
- Debug mode ativo
- SQLite para simplicidade

### Produção
- Build otimizado do React
- Debug mode desabilitado
- PostgreSQL com pooling
- Nginx para cache e compressão
