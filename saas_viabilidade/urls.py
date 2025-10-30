from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import home_redirect, dashboard_redirect
from core.admin import rm_admin_site
from core.error_views import custom_404, force_404

urlpatterns = [
    path("admin/", rm_admin_site.urls),
    # Rota genérica de dashboard que redireciona conforme papel do usuário
    path("dashboard/", dashboard_redirect, name="dashboard"),
    
    # URLs RM Systems
    path("rm/", include(("core.urls_rm", "rm"), namespace="rm")),
    
    # URLs do verificador (novo app FTTH Viewer)
    path("verificador/", include(("ftth_viewer.urls", "ftth_viewer"), namespace="verificador")),
    
    # URLs específicas por empresa
    re_path(r'^(?P<company_slug>[\w-]+)/', include(("core.urls_company", "company"), namespace="company")),
    
    # Redirect da raiz para RM
    path("", home_redirect, name="home_redirect"),
    
    # Catch-all para 404 - deve ser o último
    re_path(r'^.*$', force_404, name='catch_all_404'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
