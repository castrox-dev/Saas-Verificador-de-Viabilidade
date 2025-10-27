# Configurações para Integração Flask-Django

## 🔧 Configurações de Integração

### Flask App Settings
```python
# Configurações do Flask para integração
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True
```

### Django Integration Settings
```python
# Configurações Django para comunicação com Flask
VERIFICADOR_FLASK_URL = "http://127.0.0.1:5000"
VERIFICADOR_API_ENDPOINT = "/api/verificar"
VERIFICADOR_TIMEOUT = 30  # segundos
```

### Database Integration
```python
# Configurações de banco compartilhado (se necessário)
SHARED_DATABASE_URL = "sqlite:///shared_verificador.db"
```

### Queue System (opcional)
```python
# Configurações para processamento assíncrono
REDIS_URL = "redis://localhost:6379/2"
CELERY_BROKER_URL = "redis://localhost:6379/2"
CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
```

## 📋 Checklist de Preparação

- [ ] Flask app rodando na porta 5000
- [ ] API endpoints definidos
- [ ] Autenticação configurada
- [ ] CORS configurado para Django
- [ ] Logs configurados
- [ ] Error handling implementado

## 🔗 Endpoints Esperados

### POST /api/verificar
```json
{
    "file_path": "/path/to/file.xlsx",
    "file_type": "xlsx",
    "company_id": 1,
    "user_id": 1,
    "options": {
        "detailed_analysis": true,
        "generate_report": true
    }
}
```

### Response
```json
{
    "success": true,
    "analysis_id": "uuid-here",
    "status": "completed",
    "results": {
        "viability_score": 85,
        "issues": [],
        "recommendations": [],
        "report_url": "/reports/uuid-here.pdf"
    },
    "processing_time": 15.5
}
```

## 🚀 Comandos de Teste

```bash
# Testar Flask app
curl -X POST http://127.0.0.1:5000/api/verificar \
  -H "Content-Type: application/json" \
  -d '{"file_path": "test.xlsx", "file_type": "xlsx"}'

# Testar integração Django
python manage.py shell -c "
from core.services.verificador_service import VerificadorService
result = VerificadorService.verificar_arquivo('test.xlsx', 1, 1)
print(result)
"
```
