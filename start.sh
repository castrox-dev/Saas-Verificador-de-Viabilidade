#!/bin/bash
set -e  # Parar em caso de erro

echo "🚀 Iniciando aplicação..."

# Verificar se DATABASE_URL está configurada
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERRO: DATABASE_URL não está configurada!"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Executar migrações
echo "🗄️ Executando migrações do banco de dados..."
python manage.py migrate --noinput || {
    echo "❌ ERRO ao executar migrações!"
    exit 1
}
echo "✅ Migrações executadas com sucesso"

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || {
    echo "⚠️ AVISO: Erro ao coletar arquivos estáticos (continuando...)"
}
echo "✅ Arquivos estáticos coletados"

# Iniciar servidor
echo "🌐 Iniciando servidor Gunicorn..."
exec gunicorn saas_viabilidade.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -

