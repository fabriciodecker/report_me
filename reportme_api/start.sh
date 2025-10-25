#!/bin/bash
set -e

echo "🚀 Iniciando ReportMe API..."

# Verificar se DATABASE_URL está configurada
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não configurada!"
    echo "💡 No Railway: New → Database → PostgreSQL"
    exit 1
fi

echo "✅ DATABASE_URL configurada: ${DATABASE_URL:0:20}..."

# Verificar se as bibliotecas necessárias estão disponíveis
echo "🔍 Verificando dependências..."

python3 -c "
try:
    import psycopg2
    print('✅ PostgreSQL driver disponível')
except ImportError as e:
    print(f'❌ PostgreSQL driver não disponível: {e}')
    exit(1)

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