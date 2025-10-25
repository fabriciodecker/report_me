# 🚀 Guia de Deploy em Produção - ReportMe

## 📋 Visão Geral

Este guia detalha como fazer o deploy da aplicação ReportMe em ambiente de produção usando Docker e Docker Compose.

## 🛠️ Requisitos do Sistema

### Requisitos Mínimos
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB SSD
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Requisitos Recomendados
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD
- **Network**: 100Mbps+

## 🔧 Preparação do Servidor

### 1. Instalar Docker

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### 2. Configurar Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 3. Configurar SSL/HTTPS

```bash
# Criar diretório para certificados
mkdir -p nginx/ssl

# Opção 1: Let's Encrypt (Recomendado)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Opção 2: Certificado auto-assinado (apenas desenvolvimento)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem
```

## 📦 Deploy da Aplicação

### 1. Clone do Repositório

```bash
git clone https://github.com/seu-usuario/reportme.git
cd reportme
```

### 2. Configuração de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.prod.example .env

# Editar configurações
nano .env
```

### 3. Configurações Obrigatórias no .env

```bash
# Django
SECRET_KEY=sua-chave-secreta-super-segura-aqui
ALLOWED_HOSTS=seudominio.com,www.seudominio.com

# Banco de Dados
DB_PASSWORD=senha-muito-segura-para-postgres

# Redis
REDIS_PASSWORD=senha-muito-segura-para-redis

# Email (configurar com seu provedor)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# Monitoramento
SENTRY_DSN=https://sua-dsn-do-sentry@sentry.io/projeto

# Frontend
REACT_APP_API_URL=https://seudominio.com/api
```

### 4. Executar Deploy

```bash
# Deploy completo
./deploy.sh

# Deploy com criação de superusuário
./deploy.sh --create-superuser
```

## 🔍 Verificação do Deploy

### Serviços Disponíveis

Após o deploy bem-sucedido, os seguintes serviços estarão disponíveis:

- **Frontend**: https://seudominio.com
- **API**: https://seudominio.com/api/
- **Admin**: https://seudominio.com/admin/
- **Documentação API**: https://seudominio.com/api/docs/
- **Grafana**: http://seudominio.com:3000
- **Prometheus**: http://seudominio.com:9090

### Health Checks

```bash
# Verificar status
./maintenance.sh status

# Verificar logs
./maintenance.sh logs

# Monitorar recursos
./maintenance.sh monitor
```

## 🛡️ Configurações de Segurança

### 1. Configuração do Nginx

O arquivo `nginx.conf` já inclui:

- **Rate Limiting**: Proteção contra DDoS
- **SSL/TLS**: Configuração segura
- **Security Headers**: HSTS, CSP, etc.
- **Gzip**: Compressão de assets

### 2. Configuração do Django

O arquivo `settings_prod.py` inclui:

- **SSL**: Redirecionamento HTTPS obrigatório
- **CORS**: Configuração restritiva
- **Session Security**: Cookies seguros
- **Database**: Pool de conexões

### 3. Hardening do Sistema

```bash
# Configurar fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Desabilitar login root por SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart ssh

# Configurar backup automático
sudo crontab -e
# 0 2 * * * /caminho/para/reportme/maintenance.sh backup
```

## 📊 Monitoramento

### 1. Logs

```bash
# Logs em tempo real
./maintenance.sh logs

# Logs de serviço específico
./maintenance.sh logs api 100

# Logs do sistema
tail -f logs/reportme.log
```

### 2. Métricas

- **Grafana**: http://seudominio.com:3000
  - Dashboard de performance
  - Métricas de banco de dados
  - Alertas automáticos

- **Prometheus**: http://seudominio.com:9090
  - Métricas detalhadas
  - Histórico de performance

### 3. Alertas

Configure alertas no Sentry para:
- Erros de aplicação
- Performance degradada
- Falhas de serviço

## 🔄 Manutenção

### 1. Backup Regular

```bash
# Backup manual
./maintenance.sh backup

# Configurar backup automático (crontab)
0 2 * * * /caminho/para/reportme/maintenance.sh backup
```

### 2. Atualizações

```bash
# Atualizar aplicação
./maintenance.sh update

# Restart de serviços
./maintenance.sh restart

# Limpeza do sistema
./maintenance.sh cleanup
```

### 3. Restauração de Backup

```bash
# Listar backups
ls -la backups/

# Restaurar backup específico
gunzip backups/backup_20240101_120000.sql.gz
docker-compose -f docker-compose.prod.yml exec postgres psql -U reportme reportme < backups/backup_20240101_120000.sql
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Erro de Permissão Docker
```bash
sudo usermod -aG docker $USER
# Logout e login novamente
```

#### 2. Porta em Uso
```bash
# Verificar processos usando portas
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Parar processo conflitante
sudo systemctl stop apache2  # ou nginx
```

#### 3. Certificado SSL Inválido
```bash
# Verificar certificados
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Renovar Let's Encrypt
sudo certbot renew
```

#### 4. Banco de Dados Não Conecta
```bash
# Verificar logs do PostgreSQL
./maintenance.sh logs postgres

# Verificar conectividade
./maintenance.sh database
```

#### 5. Memória Insuficiente
```bash
# Monitorar recursos
./maintenance.sh monitor

# Ajustar workers do Gunicorn
nano .env
# GUNICORN_WORKERS=2  # Reduzir número de workers
```

### Comandos Úteis

```bash
# Status completo
./maintenance.sh status

# Restart específico
./maintenance.sh restart api

# Logs com filtro
./maintenance.sh logs api | grep ERROR

# Limpeza de espaço
./maintenance.sh cleanup
docker system prune -a
```

## 📞 Suporte

### Logs para Análise

Ao reportar problemas, inclua:

1. **Logs da aplicação**:
   ```bash
   ./maintenance.sh logs api 200
   ```

2. **Status dos serviços**:
   ```bash
   ./maintenance.sh status
   ```

3. **Recursos do sistema**:
   ```bash
   ./maintenance.sh monitor
   ```

### Contato

- **GitHub Issues**: [Criar Issue](https://github.com/seu-usuario/reportme/issues)
- **Email**: suporte@seudominio.com
- **Documentação**: https://docs.seudominio.com

---

## 📝 Checklist de Deploy

- [ ] Servidor configurado com Docker
- [ ] Firewall configurado (80, 443, 22)
- [ ] Certificados SSL instalados
- [ ] Arquivo .env configurado
- [ ] Deploy executado com sucesso
- [ ] Health checks passando
- [ ] Backup configurado
- [ ] Monitoramento ativo
- [ ] Documentação atualizada

**🎉 Parabéns! Sua aplicação ReportMe está rodando em produção!**