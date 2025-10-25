# DOCKERFILE OBRIGATÓRIO PARA RAILWAY - NÃO USAR NIXPACKS
FROM python:3.11-slim

# Força Railway a usar este Dockerfile
ENV RAILWAY_DOCKERFILE_BUILD=true
ENV NIXPACKS_BUILD_CMD="echo 'USING DOCKERFILE ONLY'"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema incluindo SQLite - MODO AGRESSIVO
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    sqlite3 \
    libsqlite3-dev \
    libsqlite3-0 \
    python3-dev \
    build-essential \
    libc6-dev \
    && ldconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalação SQLite ANTES de qualquer coisa
RUN echo "=== VERIFICAÇÃO SQLITE ===" && \
    sqlite3 --version && \
    python3 -c "import sqlite3; print('✅ SQLite3 Python OK')" && \
    ls -la /usr/lib/x86_64-linux-gnu/libsqlite3* && \
    echo "=== FIM VERIFICAÇÃO ==="

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verificar SQLite após pip install
RUN echo "=== VERIFICAÇÃO PÓS-PIP ===" && \
    python3 -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.close(); print('✅ SQLite OK')" && \
    echo "=== FIM VERIFICAÇÃO PÓS-PIP ==="

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
