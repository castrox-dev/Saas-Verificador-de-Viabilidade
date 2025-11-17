from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.http import Http404
from core import views as core_views
from core.views import home_redirect, dashboard_redirect
from core.admin import rm_admin_site
from core.error_views import custom_404, force_404
import os

urlpatterns = [
    path("admin/", rm_admin_site.urls),
    # Rota genérica de dashboard que redireciona conforme papel do usuário
    path("dashboard/", dashboard_redirect, name="dashboard"),
    
    # Mudança obrigatória de senha no primeiro acesso
    path("change-password-required/", core_views.change_password_required, name="change_password_required"),
    
    # Favicon - redireciona para o arquivo estático
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True), name="favicon"),
    
    # URLs RM Systems
    path("rm/", include(("core.urls_rm", "rm"), namespace="rm")),
    
    # URLs do verificador (novo app FTTH Viewer)
    path("verificador/", include(("ftth_viewer.urls", "ftth_viewer"), namespace="verificador")),
    
    # URLs de documentação e páginas legais (acessíveis a todos, sem autenticação)
    path("termos-uso/", core_views.termos_uso_view, name="termos_uso"),
    path("politica-privacidade/", core_views.politica_privacidade_view, name="politica_privacidade"),
    path("politica-cookies/", core_views.politica_cookies_view, name="politica_cookies"),
    path("lgpd/", core_views.lgpd_view, name="lgpd"),
    path("faq/", core_views.faq_view, name="faq"),
    path("ajuda/", core_views.ajuda_view, name="ajuda"),
    path("manual/", core_views.manual_usuario_view, name="manual_usuario"),
    
    # URLs específicas por empresa
    re_path(r'^(?P<company_slug>[\w-]+)/', include(("core.urls_company", "company"), namespace="company")),
    
    # Redirect da raiz para RM
    path("", home_redirect, name="home_redirect"),
    
    # Catch-all para 404 - deve ser o último
    re_path(r'^.*$', force_404, name='catch_all_404'),
]

# Servir arquivos de mídia (tanto em DEBUG quanto em produção no Railway)
# No Railway, os arquivos precisam ser enviados novamente após o deploy
if settings.DEBUG:
    # Em desenvolvimento, usar o método padrão
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Em produção (Railway), servir arquivos de mídia se existirem
    # NOTA: No Railway, arquivos são efêmeros - arquivos enviados localmente não estarão disponíveis
    # Arquivos precisam ser enviados novamente através da interface web após o deploy
    media_root = settings.MEDIA_ROOT
    if os.path.exists(media_root):
        urlpatterns += [
            re_path(r'^media/(?P<path>.*)$', serve, {'document_root': media_root}),
        ]
