# Dockerfile para o Backend Django
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema incluindo SQLite
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    sqlite3 \
    libsqlite3-dev \
    libsqlite3-0 \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Verificar se SQLite está instalado corretamente
RUN sqlite3 --version && python3 -c "import sqlite3; print('SQLite3 funcionando!')"

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verificar se SQLite funciona após instalação das dependências
RUN python3 -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.close(); print('✅ SQLite OK')"

# Copiar código da aplicação
COPY . .

# Copiar e dar permissão ao script de inicialização
COPY start.sh .
RUN chmod +x start.sh

# Criar usuário não-root para segurança
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Usar script de inicialização
CMD ["./start.sh"]
