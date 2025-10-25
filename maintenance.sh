#!/bin/bash
# ===================================
# Script de Manutenção - ReportMe
# ===================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Verificar status dos serviços
check_status() {
    log "Verificando status dos serviços..."
    
    echo ""
    echo "==== STATUS DOS CONTAINERS ===="
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "==== HEALTH CHECKS ===="
    
    # API
    if curl -f -s http://localhost:8000/api/core/health/ > /dev/null; then
        echo "✅ API: Saudável"
    else
        echo "❌ API: Não responde"
    fi
    
    # Nginx
    if curl -f -s http://localhost/health/ > /dev/null; then
        echo "✅ Nginx: Saudável"
    else
        echo "❌ Nginx: Não responde"
    fi
    
    # PostgreSQL
    if docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U reportme -d reportme > /dev/null 2>&1; then
        echo "✅ PostgreSQL: Saudável"
    else
        echo "❌ PostgreSQL: Não responde"
    fi
    
    # Redis
    if docker-compose -f docker-compose.prod.yml exec redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
        echo "✅ Redis: Saudável"
    else
        echo "❌ Redis: Não responde"
    fi
    
    echo ""
}

# Backup do banco de dados
backup_database() {
    log "Criando backup do banco de dados..."
    
    source .env
    
    BACKUP_DIR="backups"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$BACKUP_DIR"
    
    docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
    
    # Comprimir backup
    gzip "$BACKUP_FILE"
    
    log "Backup criado: ${BACKUP_FILE}.gz"
    
    # Limpar backups antigos (manter últimos 7 dias)
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
    
    log "Backups antigos removidos"
}

# Mostrar logs
show_logs() {
    local service="$1"
    local lines="${2:-50}"
    
    if [ -z "$service" ]; then
        log "Mostrando logs de todos os serviços (últimas $lines linhas)..."
        docker-compose -f docker-compose.prod.yml logs --tail="$lines" -f
    else
        log "Mostrando logs do serviço $service (últimas $lines linhas)..."
        docker-compose -f docker-compose.prod.yml logs --tail="$lines" -f "$service"
    fi
}

# Restart de serviços
restart_service() {
    local service="$1"
    
    if [ -z "$service" ]; then
        log "Reiniciando todos os serviços..."
        docker-compose -f docker-compose.prod.yml restart
    else
        log "Reiniciando serviço $service..."
        docker-compose -f docker-compose.prod.yml restart "$service"
    fi
}

# Atualizar aplicação
update_application() {
    log "Atualizando aplicação..."
    
    # Backup antes da atualização
    backup_database
    
    # Pull do código mais recente
    git pull origin main
    
    # Rebuild e restart
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
    
    # Executar migrações
    docker-compose -f docker-compose.prod.yml exec api python manage.py migrate
    
    # Coletar arquivos estáticos
    docker-compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput
    
    log "Aplicação atualizada com sucesso"
}

# Limpeza do sistema
cleanup_system() {
    log "Limpando sistema..."
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes não utilizados
    docker volume prune -f
    
    # Remover redes não utilizadas
    docker network prune -f
    
    # Limpar logs antigos
    find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log "Limpeza concluída"
}

# Monitoramento de recursos
monitor_resources() {
    log "Monitorando recursos do sistema..."
    
    echo ""
    echo "==== USO DE DISCO ===="
    df -h
    
    echo ""
    echo "==== USO DE MEMÓRIA ===="
    free -h
    
    echo ""
    echo "==== USO DE CPU ===="
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"% usado"}'
    
    echo ""
    echo "==== CONTAINERS DOCKER ===="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo ""
}

# Verificar conectividade de banco
check_database() {
    log "Verificando conectividade do banco de dados..."
    
    source .env
    
    # Testar conexão
    if docker-compose -f docker-compose.prod.yml exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        log "✅ Conexão com banco de dados OK"
        
        # Mostrar estatísticas
        echo ""
        echo "==== ESTATÍSTICAS DO BANCO ===="
        docker-compose -f docker-compose.prod.yml exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples
            FROM pg_stat_user_tables 
            ORDER BY n_live_tup DESC;
        "
    else
        error "❌ Falha na conexão com banco de dados"
    fi
}

# Menu de ajuda
show_help() {
    echo ""
    echo "====================================="
    echo "🔧 SCRIPT DE MANUTENÇÃO - ReportMe"
    echo "====================================="
    echo ""
    echo "Uso: $0 [comando] [opções]"
    echo ""
    echo "Comandos disponíveis:"
    echo ""
    echo "  status                 - Verificar status dos serviços"
    echo "  backup                 - Criar backup do banco de dados"
    echo "  logs [serviço] [linhas] - Mostrar logs (padrão: todos os serviços, 50 linhas)"
    echo "  restart [serviço]      - Reiniciar serviço específico ou todos"
    echo "  update                 - Atualizar aplicação do Git"
    echo "  cleanup                - Limpar sistema (imagens, volumes, logs antigos)"
    echo "  monitor                - Monitorar recursos do sistema"
    echo "  database               - Verificar conectividade e estatísticas do banco"
    echo "  help                   - Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 status"
    echo "  $0 logs api 100"
    echo "  $0 restart nginx"
    echo "  $0 backup"
    echo ""
}

# Função principal
main() {
    local command="$1"
    
    case "$command" in
        "status")
            check_status
            ;;
        "backup")
            backup_database
            ;;
        "logs")
            show_logs "$2" "$3"
            ;;
        "restart")
            restart_service "$2"
            ;;
        "update")
            update_application
            ;;
        "cleanup")
            cleanup_system
            ;;
        "monitor")
            monitor_resources
            ;;
        "database")
            check_database
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            error "Comando não reconhecido: $command"
            show_help
            ;;
    esac
}

# Executar comando
main "$@"