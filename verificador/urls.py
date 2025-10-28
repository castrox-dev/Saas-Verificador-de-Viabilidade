"""
URLs para o verificador Django
Substitui as rotas Flask
"""
from django.urls import path
from . import views

app_name = 'verificador'

urlpatterns = [
    # View principal do verificador (página com mapa)
    path('<slug:company_slug>/', views.verificador_view, name='verificador_view'),
    
    # Health check
    path('health/', views.health_check, name='health'),
    
    # Geocodificação (público - sem auth necessária)
    path('api/geocode/', views.geocode, name='geocode'),
    
    # APIs por empresa (autenticadas)
    path('<slug:company_slug>/api/verificar/', views.verificar_arquivo, name='verificar_arquivo'),
    path('<slug:company_slug>/api/verificar-viabilidade/', views.verificar_viabilidade, name='verificar_viabilidade'),
    path('<slug:company_slug>/api/arquivos/', views.listar_arquivos, name='listar_arquivos'),
    path('<slug:company_slug>/api/coordenadas/', views.obter_coordenadas, name='obter_coordenadas'),
]
