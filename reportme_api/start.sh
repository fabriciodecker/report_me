#!/bin/bash
set -e

echo "🚀 Iniciando ReportMe API..."

# Verificar qual banco será usado
if [ -n "$DATABASE_URL" ]; then
    echo "✅ DATABASE_URL configurada: ${DATABASE_URL:0:20}..."
    echo "�️ Usando PostgreSQL"
    
    # Verificar driver PostgreSQL
    python3 -c "
try:
    import psycopg2
    print('✅ PostgreSQL driver disponível')
except ImportError as e:
    print(f'❌ PostgreSQL driver não disponível: {e}')
    exit(1)
"
else
    echo "�️ Usando SQLite (sem DATABASE_URL)"
    
    # Verificar SQLite
    python3 -c "
try:
    import sqlite3
    print('✅ SQLite disponível')
except ImportError as e:
    print(f'❌ SQLite não disponível: {e}')
    exit(1)
"
fi

# Verificar Django
echo "🔍 Verificando Django..."
python3 -c "
try:
    import django
    print('✅ Django disponível')
except ImportError as e:
    print(f'❌ Django não disponível: {e}')
    exit(1)
"

echo "🗄️ Executando migrations..."
python manage.py migrate

echo "🎯 Iniciando servidor..."
exec python manage.py runserver 0.0.0.0:${PORT:-8000}