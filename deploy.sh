#!/bin/bash

# Script de deploy para rmsys.com.br
# Execute com: chmod +x deploy.sh && ./deploy.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do Verificador de Viabilidade..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    error "Execute este script no diretório raiz do projeto Django"
fi

# 1. Backup do banco atual (se existir)
log "📦 Criando backup do banco de dados..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    log "✅ Backup criado com sucesso"
else
    warning "Nenhum banco SQLite encontrado para backup"
fi

# 2. Atualizar dependências
log "📦 Instalando/atualizando dependências..."
pip install -r requirements_minimal.txt

# 3. Criar diretórios necessários
log "📁 Criando diretórios necessários..."
mkdir -p logs
mkdir -p media/cto_maps
mkdir -p staticfiles
mkdir -p backups

# 4. Configurar permissões
log "🔐 Configurando permissões..."
chmod 755 logs
chmod 755 media
chmod 755 staticfiles
chmod 600 .env  # Arquivo de ambiente deve ser restrito

# 5. Executar migrações
log "🗄️ Executando migrações do banco de dados..."
python manage.py migrate --settings=saas_viabilidade.settings_production

# 6. Coletar arquivos estáticos
log "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=saas_viabilidade.settings_production

# 7. Criar superusuário (se não existir)
log "👤 Verificando superusuário..."
python manage.py shell --settings=saas_viabilidade.settings_production << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Criando superusuário...")
    User.objects.create_superuser(
        username='admin',
        email='admin@rmsys.com.br',
        password='admin123!@#',
        first_name='Admin',
        last_name='RM Systems'
    )
    print("Superusuário criado: admin / admin123!@#")
else:
    print("Superusuário já existe")
EOF

# 8. Verificar configurações de segurança
log "🔒 Verificando configurações de segurança..."

# Verificar SECRET_KEY
if grep -q "dev-secret-key-change-me" .env; then
    error "SECRET_KEY ainda está com valor padrão! Altere no arquivo .env"
fi

# Verificar DEBUG
if grep -q "DEBUG=True" .env; then
    warning "DEBUG está habilitado em produção!"
fi

# 9. Testar configuração
log "🧪 Testando configuração..."
python manage.py check --settings=saas_viabilidade.settings_production

# 10. Configurar logs
log "📝 Configurando sistema de logs..."
touch logs/django.log
touch logs/security.log
chmod 644 logs/django.log
chmod 644 logs/security.log

# 11. Configurar supervisor (se disponível)
if command -v supervisorctl &> /dev/null; then
    log "⚙️ Configurando supervisor..."
    cat > /etc/supervisor/conf.d/saas_viabilidade.conf << EOF
[program:saas_viabilidade]
command=/path/to/venv/bin/gunicorn saas_viabilidade.wsgi:application --bind 0.0.0.0:8000
directory=/path/to/saas_viabilidade
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/saas_viabilidade.log
EOF
    supervisorctl reread
    supervisorctl update
fi

# 12. Configurar nginx (exemplo)
log "🌐 Configuração do Nginx (exemplo)..."
cat > nginx_example.conf << EOF
server {
    listen 80;
    server_name rmsys.com.br www.rmsys.com.br;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rmsys.com.br www.rmsys.com.br;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static/ {
        alias /path/to/saas_viabilidade/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /path/to/saas_viabilidade/media/;
        expires 1y;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

log "✅ Deploy concluído com sucesso!"
log "🌐 Acesse: https://rmsys.com.br"
log "👤 Login admin: admin / admin123!@#"
log "⚠️ IMPORTANTE: Altere a senha do admin imediatamente!"

echo ""
echo "📋 Próximos passos:"
echo "1. Configure o SSL/TLS no servidor"
echo "2. Configure o banco PostgreSQL"
echo "3. Configure o Redis para cache"
echo "4. Configure o backup automático"
echo "5. Configure o monitoramento (Sentry)"
echo "6. Teste todas as funcionalidades"
echo "7. Altere todas as senhas padrão"
echo ""
echo "🔒 Configurações de segurança implementadas:"
echo "✅ Middleware de segurança"
echo "✅ Validação segura de arquivos"
echo "✅ Rate limiting"
echo "✅ Headers de segurança"
echo "✅ Logging de segurança"
echo "✅ Validação de senhas complexas"
echo ""

