#!/bin/bash

# Script para desenvolvimento local do ReportMe
# Uso: ./dev.sh [comando]

set -e

case "$1" in
    "start")
        echo "🚀 Iniciando ambiente de desenvolvimento..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "stop")
        echo "🛑 Parando ambiente de desenvolvimento..."
        docker-compose -f docker-compose.dev.yml down
        ;;
    "restart")
        echo "🔄 Reiniciando ambiente de desenvolvimento..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "logs")
        echo "📜 Visualizando logs..."
        docker-compose -f docker-compose.dev.yml logs -f
        ;;
    "shell-api")
        echo "🐍 Entrando no shell do Django..."
        docker-compose -f docker-compose.dev.yml exec api python manage.py shell
        ;;
    "shell-backend")
        echo "🔧 Entrando no container do backend..."
        docker-compose -f docker-compose.dev.yml exec api bash
        ;;
    "shell-frontend")
        echo "⚛️  Entrando no container do frontend..."
        docker-compose -f docker-compose.dev.yml exec frontend sh
        ;;
    "migrate")
        echo "🗄️  Executando migrações..."
        docker-compose -f docker-compose.dev.yml exec api python manage.py migrate
        ;;
    "makemigrations")
        echo "📝 Criando migrações..."
        docker-compose -f docker-compose.dev.yml exec api python manage.py makemigrations
        ;;
    "superuser")
        echo "👤 Criando superusuário..."
        docker-compose -f docker-compose.dev.yml exec api python manage.py createsuperuser
        ;;
    "test-api")
        echo "🧪 Executando testes da API..."
        docker-compose -f docker-compose.dev.yml exec api python manage.py test
        ;;
    "test-frontend")
        echo "🧪 Executando testes do frontend..."
        docker-compose -f docker-compose.dev.yml exec frontend npm test
        ;;
    "clean")
        echo "🧹 Limpando containers e volumes..."
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -f
        ;;
    "build")
        echo "🔨 Construindo imagens..."
        docker-compose -f docker-compose.dev.yml build --no-cache
        ;;
    *)
        echo "📖 Uso: ./dev.sh [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  start          - Iniciar ambiente de desenvolvimento"
        echo "  stop           - Parar ambiente"
        echo "  restart        - Reiniciar ambiente"
        echo "  logs           - Ver logs em tempo real"
        echo "  shell-api      - Shell Django"
        echo "  shell-backend  - Shell do container backend"
        echo "  shell-frontend - Shell do container frontend"
        echo "  migrate        - Executar migrações"
        echo "  makemigrations - Criar migrações"
        echo "  superuser      - Criar superusuário"
        echo "  test-api       - Executar testes da API"
        echo "  test-frontend  - Executar testes do frontend"
        echo "  clean          - Limpar containers e volumes"
        echo "  build          - Construir imagens"
        echo ""
        echo "Exemplos:"
        echo "  ./dev.sh start"
        echo "  ./dev.sh logs"
        echo "  ./dev.sh shell-api"
        ;;
esac
