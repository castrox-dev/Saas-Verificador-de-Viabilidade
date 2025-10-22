from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'company'

urlpatterns = [
    # Autenticação da empresa
    path('login/', views.company_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Painel da empresa (para admins)
    path('painel/', views.company_dashboard, name='dashboard'),
    
    # Verificador (para todos os usuários)
    path('verificador/', views.company_verificador, name='verificador'),
    
    # Gestão de usuários da empresa (apenas admins)
    path('painel/usuarios/', views.company_user_list, name='user_list'),
    path('painel/usuarios/criar/', views.company_user_create, name='user_create'),
    path('painel/usuarios/<int:pk>/editar/', views.company_user_edit, name='user_edit'),
    path('painel/usuarios/<int:pk>/toggle/', views.company_user_toggle, name='user_toggle'),
    
    # Gestão de mapas da empresa
    path('painel/mapas/', views.company_map_list, name='map_list'),
    path('painel/mapas/upload/', views.company_map_upload, name='map_upload'),
    path('mapas/<int:pk>/download/', views.company_map_download, name='map_download'),
    path('mapas/<int:pk>/delete/', views.company_map_delete, name='map_delete'),
    
    # Upload de mapas no verificador
    path('verificador/upload/', views.company_map_upload, name='verificador_upload'),
    
    # Histórico de análises
    path('verificador/historico/', views.company_map_history, name='map_history'),
]