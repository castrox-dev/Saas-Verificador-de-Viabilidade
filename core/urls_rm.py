from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'rm'

urlpatterns = [
    # Autenticação RM
    path('login/', views.rm_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Painel administrativo RM
    path('admin/', views.rm_admin_dashboard, name='admin_dashboard'),
    
    # Gestão de empresas
    path('empresas/', views.rm_company_list, name='company_list'),
    path('empresas/criar/', views.rm_company_create, name='company_create'),
    path('empresas/<int:pk>/editar/', views.rm_company_edit, name='company_edit'),
    path('empresas/<int:pk>/toggle/', views.rm_company_toggle, name='company_toggle'),
    
    # Gestão de usuários (visão global)
    path('usuarios/', views.rm_user_list, name='user_list'),
    path('usuarios/criar/', views.rm_user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.rm_user_edit, name='user_edit'),
    path('usuarios/<int:pk>/toggle/', views.rm_user_toggle, name='user_toggle'),
    
    # Gestão de mapas (visão global)
    path('mapas/', views.rm_map_list, name='map_list'),
    path('mapas/<int:pk>/download/', views.rm_map_download, name='map_download'),
    path('mapas/<int:pk>/delete/', views.rm_map_delete, name='map_delete'),
    
    # Estatísticas e relatórios
    path('relatorios/', views.rm_reports, name='reports'),
]