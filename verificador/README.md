# Verificador de Viabilidade FTTH - SaaS

Sistema integrado de verificação de viabilidade para instalações FTTH (Fiber to the Home) no contexto SaaS.

## 🚀 Funcionalidades

### **Sistema SaaS Integrado**
- **Multi-empresa**: Cada empresa tem seus próprios mapas e configurações
- **Autenticação**: Sistema de login integrado com controle de acesso
- **Isolamento de dados**: Dados separados por empresa
- **Interface administrativa**: Painel de controle para gerenciar empresas e usuários

### **Verificação de Viabilidade**
- **Upload de mapas**: Suporte a KML, KMZ, CSV, Excel (XLS/XLSX)
- **Cálculo de distâncias**: Integração com OSRM para rotas reais
- **Classificação automática**: Viável, Limitada, Sem viabilidade
- **Cache inteligente**: Sistema de cache para melhor performance

### **Geocodificação**
- **OpenStreetMap**: Integração com Nominatim
- **Cache persistente**: Armazenamento de resultados para reutilização
- **Fallback**: Múltiplas estratégias de busca

### **APIs REST**
- **Públicas**: Acesso sem autenticação para funcionalidades básicas
- **Autenticadas**: APIs específicas por empresa
- **Documentação**: Endpoints bem documentados

## 🏗️ Arquitetura

### **Estrutura do Projeto**
```
verificador/
├── models.py              # Modelos de dados (Cache, CTOs)
├── views.py               # Views e APIs (Públicas + Autenticadas)
├── services.py            # Lógica de negócio principal
├── file_readers.py        # Leitura de arquivos (KML, KMZ, CSV, Excel)
├── geocoding.py           # Serviço de geocodificação
├── routing.py             # Cálculo de rotas e distâncias
├── utils.py               # Utilitários e helpers
├── admin.py               # Interface administrativa
├── tests.py               # Testes de integração
├── templates/             # Templates HTML
│   └── verificador/
│       ├── index.html     # Interface principal (mapa completo)
│       └── verificador.html # Interface simples
└── static/                # Arquivos estáticos
    └── verificador/
        ├── css/           # Estilos
        ├── js/            # JavaScript
        └── images/        # Imagens
```

### **Integração com Sistema SaaS**
- **Core App**: Usuários, empresas, autenticação
- **Verificador App**: Funcionalidades FTTH específicas
- **Isolamento**: Dados separados por empresa
- **Cache compartilhado**: Sistema de cache unificado

## 📋 APIs Disponíveis

### **APIs Públicas (Sem Autenticação)**

#### **Geocodificação**
```http
GET /verificador/api/geocode/?endereco=Rua das Flores, 123, Rio de Janeiro
```
**Resposta:**
```json
{
    "lat": -22.9068,
    "lng": -43.1729,
    "endereco_completo": "Rua das Flores, 123, Rio de Janeiro, RJ, Brasil"
}
```

#### **Listagem de Arquivos FTTH**
```http
GET /verificador/api/arquivos/
```
**Resposta:**
```json
[
    {
        "nome": "ctos_rio.kml",
        "tipo": "kml",
        "total_pontos": 150,
        "ativo": true
    }
]
```

#### **Coordenadas de CTOs**
```http
GET /verificador/api/coordenadas/
```
**Resposta:**
```json
[
    {
        "nome": "CTO 001",
        "lat": -22.9068,
        "lng": -43.1729,
        "arquivo": "ctos_rio.kml",
        "fonte": "global"
    }
]
```

#### **Verificação de Viabilidade**
```http
GET /verificador/api/verificar-viabilidade/?lat=-22.9068&lon=-43.1729
```
**Resposta:**
```json
{
    "viabilidade": {
        "status": "Viável",
        "distancia": 250.5,
        "cto_mais_proximo": {
            "nome": "CTO 001",
            "lat": -22.9068,
            "lng": -43.1729,
            "distancia": 250.5
        }
    },
    "tempo_resposta": 1.2
}
```

#### **Estatísticas do Cache**
```http
GET /verificador/api/cache/geocoding/stats/
```
**Resposta:**
```json
{
    "total_entries": 1250,
    "valid_entries": 1200,
    "cache_hit_rate": 0.85,
    "oldest_entry": "2024-01-15T10:30:00Z",
    "newest_entry": "2024-01-20T15:45:00Z"
}
```

#### **Limpeza do Cache**
```http
POST /verificador/api/cache/geocoding/clear/
```

### **APIs Autenticadas (Por Empresa)**

#### **Verificação de Arquivo da Empresa**
```http
GET /verificador/{company_slug}/api/verificar/
```

#### **Verificação de Viabilidade da Empresa**
```http
GET /verificador/{company_slug}/api/verificar-viabilidade/?lat=-22.9068&lon=-43.1729
```

#### **Arquivos da Empresa**
```http
GET /verificador/{company_slug}/api/arquivos/
```

#### **Coordenadas da Empresa**
```http
GET /verificador/{company_slug}/api/coordenadas/
```

## ⚙️ Configuração

### **Diretórios de Mapas**
```python
# settings.py
FTTH_MAPAS_ROOT = BASE_DIR / 'Mapas'
FTTH_KML_DIR = FTTH_MAPAS_ROOT / 'kml'
FTTH_KMZ_DIR = FTTH_MAPAS_ROOT / 'kmz'
FTTH_CSV_DIR = FTTH_MAPAS_ROOT / 'csv'
FTTH_XLS_DIR = FTTH_MAPAS_ROOT / 'xls'
FTTH_XLSX_DIR = FTTH_MAPAS_ROOT / 'xlsx'
```

### **Configurações de Viabilidade**
```python
# settings.py
FTTH_VIABILIDADE_CONFIG = {
    'viavel': 300,      # Até 300m = Viável
    'limitada': 800,    # 300-800m = Viabilidade Limitada
    'inviavel': 800     # Acima de 800m = Sem Viabilidade
}
```

### **Configurações de Roteamento**
```python
# settings.py
ROUTING_TIMEOUT = 15  # Timeout em segundos
ENABLE_ROUTE_CACHE = True
MAX_CACHE_SIZE = 1000

# OpenRouteService API Key (opcional)
OPENROUTESERVICE_API_KEY = 'sua_api_key_aqui'
```

## 🧪 Testes

### **Executar Testes**
```bash
# Todos os testes
python manage.py test verificador

# Testes específicos
python manage.py test verificador.tests.VerificadorIntegrationTests
python manage.py test verificador.tests.VerificadorPerformanceTests

# Teste individual
python manage.py test verificador.tests.VerificadorIntegrationTests.test_geocoding_cache
```

### **Tipos de Testes**
- **Testes de Integração**: APIs, views, serviços
- **Testes de Performance**: Cache, otimizações
- **Testes de Funcionalidade**: Geocodificação, classificação

## 🚀 Performance

### **Sistema de Cache**
- **Cache de Geocodificação**: Persistente no banco de dados
- **Cache de CTOs**: Memória (1 hora)
- **Cache de Viabilidade**: Persistente no banco de dados
- **Cache de Empresa**: Memória (30 minutos)

### **Otimizações**
- **Processamento paralelo**: ThreadPoolExecutor para rotas
- **Cache inteligente**: Múltiplas camadas de cache
- **Tratamento de erros**: Fallbacks e recuperação
- **Logging**: Sistema de logs detalhado

## 📊 Monitoramento

### **Health Check**
```http
GET /verificador/health/
```
**Resposta:**
```json
{
    "status": "online",
    "service": "Django Verificador",
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "1.0.0"
}
```

### **Logs**
- **Geocodificação**: Sucessos e falhas
- **Roteamento**: Tempos de resposta
- **Cache**: Hit/miss rates
- **Erros**: Stack traces completos

## 🔧 Desenvolvimento

### **Estrutura de Dados**

#### **Modelos Principais**
- **GeocodingCache**: Cache de geocodificação
- **ViabilidadeCache**: Cache de verificações
- **CTOFile**: Arquivos de CTOs processados

#### **Integração com Core**
- **Company**: Empresas do sistema SaaS
- **CustomUser**: Usuários com roles
- **CTOMapFile**: Mapas por empresa

### **Padrões de Código**
- **Services**: Lógica de negócio isolada
- **Utils**: Funções auxiliares reutilizáveis
- **Cache**: Estratégias de cache consistentes
- **Error Handling**: Tratamento robusto de erros

## 📈 Roadmap

### **Próximas Funcionalidades**
- [ ] **Dashboard Analytics**: Métricas de uso e performance
- [ ] **API Rate Limiting**: Controle de taxa de requisições
- [ ] **Webhooks**: Notificações em tempo real
- [ ] **Batch Processing**: Processamento em lote
- [ ] **Exportação**: Relatórios em PDF/Excel

### **Melhorias Técnicas**
- [ ] **Redis Cache**: Cache distribuído
- [ ] **Celery Tasks**: Processamento assíncrono
- [ ] **API Versioning**: Controle de versões
- [ ] **Metrics**: Prometheus/Grafana
- [ ] **Load Testing**: Testes de carga

## 📄 Licença

Este projeto está sob a licença MIT.

---

**Desenvolvido com ❤️ para o ecossistema FTTH brasileiro**