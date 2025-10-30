from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, test_views

app_name = 'rm'

urlpatterns = [
    # Autenticação RM
    path('login/', views.rm_login_view, name='login'),
    # Troca LogoutView por view própria para aceitar GET e redirecionar corretamente
    path('logout/', views.logout_view, name='logout'),
    
    # Painel administrativo RM
    path('admin/', views.rm_admin_dashboard, name='admin_dashboard'),
    
    # Gestão de empresas
    path('empresas/', views.company_list, name='company_list'),
    path('empresas/criar/', views.rm_company_create, name='company_create'),
    path('empresas/<int:company_id>/editar/', views.rm_company_edit, name='company_edit'),
    path('empresas/<int:company_id>/delete/', views.rm_company_delete, name='company_delete'),
    # Portal de gestão específico da empresa (RM)
    path('empresas/<slug:company_slug>/painel/', views.rm_company_portal, name='company_portal'),
    # Checagem de login para acessar o portal de gestão
    path('empresas/<slug:company_slug>/login-check/', views.rm_company_login_check, name='company_login_check'),
    
    # Gestão de usuários (visão global)
    path('usuarios/', views.rm_user_list, name='user_list'),
    path('usuarios/quick-search/', views.rm_user_quick_search, name='user_quick_search'),
    path('usuarios/criar/', views.rm_user_create, name='user_create'),
    path('usuarios/<int:user_id>/editar/', views.rm_user_edit, name='user_edit'),
    path('usuarios/<int:user_id>/detalhes/', views.rm_user_details, name='user_details'),
    path('usuarios/<int:user_id>/delete/', views.rm_user_delete, name='user_delete'),
    
    # Gestão de mapas (visão global)
    path('mapas/', views.rm_map_list, name='map_list'),
    path('mapas/por-empresa/', views.rm_maps_by_company, name='map_by_company'),
    path('mapas/download/<int:pk>/', views.rm_map_download, name='map_download'),
    path('mapas/delete/<int:pk>/', views.rm_map_delete, name='map_delete'),

    # Relatórios RM
    path('relatorios/', views.rm_reports, name='reports'),
    path('relatorios/exportar/csv/', views.rm_reports_export_csv, name='reports_export_csv'),
    
    # Páginas de teste de erro (apenas em DEBUG)
    path('test/404/', test_views.test_404, name='test_404'),
    path('test/500/', test_views.test_500, name='test_500'),
    path('test/403/', test_views.test_403, name='test_403'),
    path('test/400/', test_views.test_400, name='test_400'),
    
    # URL para forçar 404 e testar página personalizada
    path('test-404/', test_views.force_404, name='force_404'),
    path('show-404/', test_views.show_404_page, name='show_404'),
]