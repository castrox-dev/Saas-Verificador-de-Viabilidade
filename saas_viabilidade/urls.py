from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import home_redirect, dashboard_redirect
from core.admin import rm_admin_site

urlpatterns = [
    path("admin/", rm_admin_site.urls),
    # Rota genérica de dashboard que redireciona conforme papel do usuário
    path("dashboard/", dashboard_redirect, name="dashboard"),
    
    # URLs RM Systems
    path("rm/", include(("core.urls_rm", "rm"), namespace="rm")),
    
    # URLs específicas por empresa
    re_path(r'^(?P<company_slug>[\w-]+)/', include(("core.urls_company", "company"), namespace="company")),
    
    # Redirect da raiz para RM
    path("", home_redirect, name="home_redirect"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
