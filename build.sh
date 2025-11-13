#!/bin/bash
# Script de build para Railway/Deploy

set -e  # Para na primeira falha

echo "🔧 Instalando dependências..."
pip install -r requirements.txt

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"

