#!/bin/bash
# Script de backup do banco de dados para VPS
# Use com crontab para backups automáticos

set -e

# Configurações
BACKUP_DIR="/var/backups/saas-viabilidade"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Carregar DATABASE_URL do .env
ENV_FILE="/var/www/saas-viabilidade/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Arquivo .env não encontrado: $ENV_FILE"
    exit 1
fi

export $(cat "$ENV_FILE" | grep -v '^#' | grep DATABASE_URL | xargs)

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL não configurada no .env"
    exit 1
fi

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# Nome do arquivo de backup
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

echo "📦 Iniciando backup do banco de dados..."
echo "   Arquivo: $BACKUP_FILE"

# Fazer backup
if pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"; then
    echo "✅ Backup criado com sucesso: $BACKUP_FILE"
    
    # Calcular tamanho do arquivo
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "   Tamanho: $SIZE"
    
    # Remover backups antigos
    echo "🗑️ Removendo backups antigos (> $RETENTION_DAYS dias)..."
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    # Listar backups atuais
    echo ""
    echo "📋 Backups atuais:"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | tail -5 || echo "   Nenhum backup encontrado"
    
    exit 0
else
    echo "❌ Erro ao criar backup!"
    exit 1
fi

