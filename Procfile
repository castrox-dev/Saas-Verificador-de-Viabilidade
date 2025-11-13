web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn saas_viabilidade.wsgi:application --bind 0.0.0.0:$PORT

