from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from . import views
from ftth_viewer import views as ftth_views

app_name = 'company'

urlpatterns = [
    # Autenticação da empresa
    path('login/', views.company_login_view, name='login'),
    # Troca LogoutView por view própria que aceita GET e redireciona para login da empresa
    path('logout/', views.company_logout_view, name='logout'),
    
    # Painel da empresa (para admins)
    path('painel/', views.company_dashboard, name='dashboard'),
    
    # Rota nomeada compatível para links antigos: company:verificador
    path('verificador/', ftth_views.index, name='verificador'),
    # Rotas explícitas para evitar 404 em chamadas diretas via fetch
    path('verificador/api/verificar-viabilidade', ftth_views.api_verificar_viabilidade, name='api_verificar_viabilidade_company'),
    path('verificador/api/verificar-viabilidade/', ftth_views.api_verificar_viabilidade),
    re_path(r'^verificador/api/verificar-viabilidade/?$', ftth_views.api_verificar_viabilidade),
    path('verificador/api/arquivos', ftth_views.api_arquivos, name='api_arquivos_company'),
    path('verificador/api/arquivos/', ftth_views.api_arquivos),
    path('verificador/api/coordenadas', ftth_views.api_coordenadas, name='api_coordenadas_company'),
    path('verificador/api/coordenadas/', ftth_views.api_coordenadas),
    
    # Upload de mapas CTO (página de upload)
    path('upload/', views.company_map_upload_page, name='upload'),
    path('upload/arquivo/', views.company_map_upload, name='map_upload'),
    path('verificar-coordenadas/', views.company_verificar_coordenadas, name='verificar_coordenadas'),
    
    # Gestão de usuários da empresa (apenas admins)
    path('painel/usuarios/', views.company_user_list, name='user_list'),
    path('painel/usuarios/criar/', views.company_user_create, name='user_create'),
    path('painel/usuarios/<int:user_id>/editar/', views.company_user_edit, name='user_edit'),
    path('painel/usuarios/<int:user_id>/toggle/', views.company_user_toggle, name='user_toggle'),
    
    # Gestão de mapas da empresa
    path('painel/mapas/', views.company_map_list, name='map_list'),
    path('painel/mapas/admin/', views.company_map_admin, name='map_admin'),
    path('mapas/<int:pk>/download/', views.company_map_download, name='map_download'),
    path('mapas/<int:pk>/delete/', views.company_map_delete, name='map_delete'),
    
    # Histórico de análises
    path('verificador/historico/', views.company_map_history, name='map_history'),
]