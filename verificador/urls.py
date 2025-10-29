"""
URLs para o verificador Django
Substitui as rotas Flask
"""
from django.urls import path
from . import views

app_name = 'verificador'

urlpatterns = [
    # View principal do verificador (página com mapa completo)
    path('<slug:company_slug>/', views.verificador_view, name='verificador_view'),
    
    # View principal do verificador (página com mapa interativo completo)
    path('<slug:company_slug>/mapa/', views.verificador_mapa_view, name='verificador_mapa'),
    
    # Health check
    path('health/', views.health_check, name='health'),
    
    # Geocodificação (público - sem auth necessária)
    path('api/geocode/', views.geocode, name='geocode'),
    
    # APIs FTTH (públicas - sem auth necessária)
    path('api/arquivos/', views.api_arquivos_ftth, name='api_arquivos_ftth'),
    path('api/coordenadas/', views.api_coordenadas_ftth, name='api_coordenadas_ftth'),
    path('api/contar-pontos/', views.api_contar_pontos, name='api_contar_pontos'),
    path('api/verificar-viabilidade/', views.api_verificar_viabilidade_ftth, name='api_verificar_viabilidade_ftth'),
    path('api/cache/geocoding/stats/', views.api_cache_geocoding_stats, name='api_cache_geocoding_stats'),
    path('api/cache/geocoding/clear/', views.api_cache_geocoding_clear, name='api_cache_geocoding_clear'),
    
    # APIs por empresa (autenticadas)
    path('<slug:company_slug>/api/verificar/', views.verificar_arquivo, name='verificar_arquivo'),
    path('<slug:company_slug>/api/verificar-viabilidade/', views.verificar_viabilidade, name='verificar_viabilidade'),
    path('<slug:company_slug>/api/arquivos/', views.listar_arquivos, name='listar_arquivos'),
    path('<slug:company_slug>/api/coordenadas/', views.obter_coordenadas, name='obter_coordenadas'),
]
