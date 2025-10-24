# Deploy do ReportMe API

Este documento explica como fazer deploy da aplicação em diferentes plataformas.

## 🚀 Deploy no Railway (Recomendado)

### 1. Preparação
```bash
# 1. Faça commit de todas as alterações
git add .
git commit -m "Preparando para deploy"

# 2. Envie para o GitHub
git push origin main
```

### 2. Deploy no Railway
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório do seu projeto
6. O Railway detectará automaticamente o Dockerfile

### 3. Configurar Variáveis de Ambiente
No painel do Railway, vá em "Variables" e adicione:
```
SECRET_KEY=your-super-secret-production-key
DEBUG=False
ALLOWED_HOSTS=*.railway.app
FRONTEND_URL=https://your-app.railway.app
```

### 4. Configurar Banco de Dados (Opcional)
- Clique em "New" → "Database" → "PostgreSQL"
- O Railway automaticamente conectará ao Django

## 🔧 Deploy no Render

### 1. Preparação
1. Acesse [render.com](https://render.com)
2. Conecte com GitHub
3. Clique em "New Web Service"
4. Selecione seu repositório

### 2. Configurações
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT`
- **Environment**: Python 3

### 3. Variáveis de Ambiente
```
SECRET_KEY=your-super-secret-production-key
DEBUG=False
ALLOWED_HOSTS=*.onrender.com
```

## 🌊 Deploy no DigitalOcean App Platform

### 1. Preparação
1. Acesse [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Vá em "Apps" → "Create App"
3. Conecte com GitHub

### 2. Configurações
- O DigitalOcean detectará automaticamente o Dockerfile
- Configure as variáveis de ambiente no painel

## 📋 Checklist Pré-Deploy

- [ ] Todas as dependências estão no `requirements.txt`
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] Variáveis de ambiente definidas
- [ ] Banco de dados configurado (se necessário)
- [ ] Configurações de email definidas

## 🔐 Segurança

### Gerar SECRET_KEY segura:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### ALLOWED_HOSTS por plataforma:
- **Railway**: `*.railway.app`
- **Render**: `*.onrender.com`
- **DigitalOcean**: `*.ondigitalocean.app`
- **Heroku**: `*.herokuapp.com`

## 🗄️ Banco de Dados

Para produção, recomendo PostgreSQL. As plataformas oferecem:

- **Railway**: PostgreSQL gratuito
- **Render**: PostgreSQL gratuito (limitado)
- **DigitalOcean**: Banco gerenciado (pago)

## 📧 Email em Produção

Configure um provedor SMTP:
- Gmail (com senha de app)
- SendGrid
- Mailgun
- Amazon SES

## 🔍 Monitoramento

Após o deploy:
- Verifique os logs da aplicação
- Teste todas as funcionalidades
- Configure SSL (automático na maioria das plataformas)
- Configure domínio customizado (opcional)

## 🆘 Troubleshooting

### Erro de SECRET_KEY
```
django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.
```
**Solução**: Configure a variável SECRET_KEY nas configurações da plataforma.

### Erro de ALLOWED_HOSTS
```
DisallowedHost at /
```
**Solução**: Adicione o domínio da plataforma em ALLOWED_HOSTS.

### Erro de Database
```
django.db.utils.OperationalError: could not connect to server
```
**Solução**: Verifique as configurações do banco de dados.