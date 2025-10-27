# Configurações da aplicação FTTH KML Viewer

# ===== ROTEAMENTO 100% GRATUITO =====
# Este sistema usa apenas APIs gratuitas para roteamento:
# 1. OSRM (Open Source Routing Machine) - Totalmente gratuito
# 2. OpenRouteService - 2000 requisições gratuitas por dia
# 3. GraphHopper - Limitado mas gratuito
# 4. Linha reta - Fallback final

# OpenRouteService API Key (GRATUITA - 2000 requests/dia)
# Para obter: https://openrouteservice.org/dev/#/signup
# Substitua pela sua chave gratuita para melhor qualidade
OPENROUTESERVICE_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjcwNDUxNjA4ZTY0OTQxMjBhNjZhZWQ0MGU2NGJiZGUwIiwiaCI6Im11cm11cjY0In0='

# Configurações de roteamento
ROUTING_TIMEOUT = 15  # Timeout em segundos para APIs de roteamento
ENABLE_ROUTE_CACHE = True  # Habilitar cache de rotas
MAX_CACHE_SIZE = 1000  # Máximo de rotas no cache

# Configurações de viabilidade (distâncias em metros)
VIABILIDADE_CONFIG = {
    'viavel': 300,      # Até 300m = Viável
    'limitada': 800,    # 300-800m = Viabilidade Limitada  
    'inviavel': 800     # Acima de 800m = Sem Viabilidade
}