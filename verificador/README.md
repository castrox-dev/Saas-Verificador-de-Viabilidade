# App Verificador Django

App Django dedicado para verificação de viabilidade de mapas CTO.

## 📁 Estrutura

```
verificador/
├── __init__.py
├── apps.py              # Configuração do app
├── models.py            # Modelos (atualmente vazio, usa core.models)
├── views.py             # API endpoints
├── urls.py              # Rotas da API
├── admin.py             # Admin Django
├── tests.py             # Testes
├── migrations/          # Migrações do banco
├── templates/           # Templates HTML
│   └── verificador/
│       └── company_verifier.html
├── file_readers.py      # Leitura de KML, KMZ, CSV, Excel
├── routing.py           # Roteamento OSRM
├── geocoding.py         # Geocodificação
└── services.py          # Serviço principal
```

## 🚀 Funcionalidades

### 1. Leitura de Arquivos
- **KML**: Arquivos Keyhole Markup Language
- **KMZ**: Arquivos KMZ (KML comprimido)
- **CSV**: Arquivos CSV com coordenadas
- **Excel**: Arquivos XLS e XLSX

### 2. Roteamento
- **OSRM**: Roteamento por ruas (API gratuita)
- **Haversine**: Cálculo de distância euclidiana
- **Cache**: Sistema de cache Django

### 3. Geocodificação
- **OpenStreetMap Nominatim**: API gratuita
- **Cache**: Cache de 24h

### 4. Verificação de Viabilidade
- Classificação automática por distância
- Processamento paralelo
- Integração com core.models.CTOMapFile

## 📍 URLs

### APIs
```
GET  /verificador/health/
GET  /verificador/api/geocode/
POST /verificador/{company_slug}/api/verificar/
GET  /verificador/{company_slug}/api/verificar-viabilidade/
GET  /verificador/{company_slug}/api/arquivos/
GET  /verificador/{company_slug}/api/coordenadas/
```

### Interface Web
```
/{company_slug}/verificador/
```

## 🔧 Dependências

- `pandas` - Processamento de CSV/Excel
- `openpyxl` - Leitura de Excel
- `requests` - Chamadas HTTP para APIs externas

## 📦 Uso

O app é integrado automaticamente ao Django através do `INSTALLED_APPS` em `settings.py`.

### Importar serviços:
```python
from verificador.services import VerificadorService
from verificador.geocoding import GeocodingService
from verificador.file_readers import FileReaderService
from verificador.routing import RoutingService
```

### Exemplo de uso:
```python
# Verificar arquivo
result = VerificadorService.verificar_arquivo(file_path, file_type)

# Verificar coordenadas
result = VerificadorService.verificar_viabilidade_coordenada(lat, lon, company)

# Geocodificar endereço
result = GeocodingService.geocodificar("Rua Exemplo, 123")
```

## 🔐 Segurança

- Todas as APIs de empresa requerem autenticação
- Verificação de acesso multi-tenant
- Isolamento por empresa

## 📝 Notas

- O app não tem modelos próprios (usa `core.models`)
- Templates estão em `verificador/templates/verificador/`
- Integração com `core.verificador_service` para compatibilidade

## 🎯 Próximos Passos

- Adicionar modelos próprios (ex: VerificacaoLog)
- Implementar testes unitários
- Adicionar processamento assíncrono (Celery)
- Criar API REST completa documentada
