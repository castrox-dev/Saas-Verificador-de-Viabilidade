from django.urls import path
from .views import (
    home, dashboard, download_file, delete_file,
    login_view, logout_view,
    company_list, company_create, company_edit,
    user_list, user_create, user_edit,
    map_list,
    toggle_user_status, toggle_company_status
)

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    
    # URLs para empresas
    path("companies/", company_list, name="company_list"),
    path("companies/create/", company_create, name="company_create"),
    path("companies/<int:company_id>/edit/", company_edit, name="company_edit"),
    
    # URLs para usuários
    path("users/", user_list, name="user_list"),
    path("users/create/", user_create, name="user_create"),
    path("users/<int:user_id>/edit/", user_edit, name="user_edit"),
    
    # URLs para mapas
    path("maps/", map_list, name="map_list"),
    path("download/<int:file_id>/", download_file, name="download_file"),
    path("delete/<int:file_id>/", delete_file, name="delete_file"),
    
    # URLs AJAX
    path("ajax/toggle-user/<int:user_id>/", toggle_user_status, name="toggle_user_status"),
    path("ajax/toggle-company/<int:company_id>/", toggle_company_status, name="toggle_company_status"),
]