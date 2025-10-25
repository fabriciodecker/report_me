#!/bin/bash
# ===================================
# Script de Deploy para Produção - ReportMe
# ===================================

set -e  # Para execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificações preliminares
check_requirements() {
    log "Verificando requisitos do sistema..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado"
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado"
    fi
    
    # Verificar Git
    if ! command -v git &> /dev/null; then
        error "Git não está instalado"
    fi
    
    log "Todos os requisitos foram atendidos"
}

# Configurar variáveis de ambiente
setup_environment() {
    log "Configurando variáveis de ambiente..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.prod.example" ]; then
            warning "Arquivo .env não encontrado. Copiando de .env.prod.example"
            cp .env.prod.example .env
            error "Por favor, configure as variáveis em .env antes de continuar"
        else
            error "Arquivo .env.prod.example não encontrado"
        fi
    fi
    
    # Verificar variáveis críticas
    source .env
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-here-change-this-in-production" ]; then
        error "SECRET_KEY não configurada. Configure em .env"
    fi
    
    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "your-secure-database-password-here" ]; then
        error "DB_PASSWORD não configurada. Configure em .env"
    fi
    
    log "Variáveis de ambiente configuradas"
}

# Criar diretórios necessários
create_directories() {
    log "Criando diretórios necessários..."
    
    mkdir -p logs
    mkdir -p backups
    mkdir -p nginx/ssl
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    log "Diretórios criados"
}

# Backup do banco de dados (se existir)
backup_database() {
    log "Criando backup do banco de dados..."
    
    if docker ps -q -f name=reportme_postgres > /dev/null; then
        BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
        docker exec reportme_postgres pg_dump -U reportme reportme > "$BACKUP_FILE"
        log "Backup criado: $BACKUP_FILE"
    else
        info "Nenhum banco de dados encontrado para backup"
    fi
}

# Build das imagens Docker
build_images() {
    log "Construindo imagens Docker..."
    
    # Parar containers existentes
    docker-compose -f docker-compose.prod.yml down
    
    # Build das imagens
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log "Imagens construídas com sucesso"
}

# Inicializar banco de dados
init_database() {
    log "Inicializando banco de dados..."
    
    # Aguardar PostgreSQL estar pronto
    log "Aguardando PostgreSQL..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # Esperar o banco estar pronto
    for i in {1..30}; do
        if docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U reportme -d reportme; then
            break
        fi
        echo "Aguardando banco de dados... ($i/30)"
        sleep 2
    done
    
    # Executar migrações
    log "Executando migrações..."
    docker-compose -f docker-compose.prod.yml run --rm api python manage.py migrate
    
    # Coletar arquivos estáticos
    log "Coletando arquivos estáticos..."
    docker-compose -f docker-compose.prod.yml run --rm api python manage.py collectstatic --noinput
    
    log "Banco de dados inicializado"
}

# Criar superusuário (opcional)
create_superuser() {
    if [ "$1" = "--create-superuser" ]; then
        log "Criando superusuário..."
        docker-compose -f docker-compose.prod.yml run --rm api python manage.py createsuperuser
    fi
}

# Iniciar serviços
start_services() {
    log "Iniciando todos os serviços..."
    
    docker-compose -f docker-compose.prod.yml up -d
    
    # Verificar se todos os serviços estão rodando
    log "Verificando status dos serviços..."
    sleep 10
    
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log "Serviços iniciados com sucesso!"
        
        echo ""
        echo "====================================="
        echo "🚀 DEPLOY CONCLUÍDO COM SUCESSO! 🚀"
        echo "====================================="
        echo ""
        echo "Serviços disponíveis:"
        echo "• Frontend: https://localhost"
        echo "• API: https://localhost/api/"
        echo "• Admin: https://localhost/admin/"
        echo "• Docs API: https://localhost/api/docs/"
        echo "• Grafana: http://localhost:3000"
        echo "• Prometheus: http://localhost:9090"
        echo ""
        echo "Para verificar logs:"
        echo "docker-compose -f docker-compose.prod.yml logs -f"
        echo ""
        echo "Para parar os serviços:"
        echo "docker-compose -f docker-compose.prod.yml down"
        echo ""
    else
        error "Alguns serviços falharam ao iniciar. Verifique os logs."
    fi
}

# Verificar saúde dos serviços
health_check() {
    log "Verificando saúde dos serviços..."
    
    # API Health Check
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/core/health/ &> /dev/null; then
            log "✅ API está saudável"
            break
        fi
        echo "Aguardando API... ($i/30)"
        sleep 2
    done
    
    # Nginx Health Check
    if curl -f http://localhost/health/ &> /dev/null; then
        log "✅ Nginx está saudável"
    else
        warning "❌ Nginx não está respondendo"
    fi
}

# Função principal
main() {
    echo "====================================="
    echo "🚀 DEPLOY REPORTME PRODUÇÃO"
    echo "====================================="
    echo ""
    
    check_requirements
    setup_environment
    create_directories
    backup_database
    build_images
    init_database
    create_superuser "$1"
    start_services
    health_check
}

# Executar função principal com argumentos
main "$@"