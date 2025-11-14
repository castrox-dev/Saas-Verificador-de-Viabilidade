from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar headers de segurança
    """
    
    def process_response(self, request, response):
        # Headers específicos para Service Worker
        # Verificar tanto /sw.js quanto /static/js/sw.js ou staticfiles/js/sw.js
        sw_paths = ['/sw.js', '/service-worker.js', 'static/js/sw.js', 'staticfiles/js/sw.js']
        is_service_worker = any(
            request.path.endswith(path) or path in request.path or 
            request.path.startswith('/static/') and 'sw.js' in request.path
            for path in sw_paths
        )
        
        if is_service_worker:
            response['Content-Type'] = 'application/javascript; charset=utf-8'
            response['Service-Worker-Allowed'] = '/'
            # Service Workers não devem ser cacheados
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            # Log apenas em desenvolvimento
            if settings.DEBUG:
                logger.debug(f"Service Worker headers aplicados para: {request.path}")
        
        # Headers específicos para manifest.json
        if request.path.endswith('/manifest.json'):
            response['Content-Type'] = 'application/manifest+json; charset=utf-8'
        
        # Content Security Policy - Restritivo mas permitindo estilos inline para desenvolvimento
        # Permite arquivos estáticos do próprio domínio
        request_host = request.get_host()
        # Remover porta se presente para CSP (CSP não aceita portas)
        host_without_port = request_host.split(':')[0]
        protocol = 'https' if request.is_secure() else 'http'
        
        csp = (
            f"default-src 'self' {protocol}://{host_without_port}; "
            f"script-src 'self' 'unsafe-inline' {protocol}://{host_without_port} https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com https://www.gstatic.com; "
            f"style-src 'self' 'unsafe-inline' {protocol}://{host_without_port} https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://unpkg.com https://www.gstatic.com; "
            f"font-src 'self' data: blob: {protocol}://{host_without_port} https://fonts.gstatic.com https://fonts.googleapis.com https://cdnjs.cloudflare.com https://unpkg.com https://cdn.jsdelivr.net https://use.fontawesome.com https://ka-f.fontawesome.com https://pro.fontawesome.com https://kit.fontawesome.com; "
            f"img-src 'self' data: blob: {protocol}://{host_without_port} https:; "
            f"connect-src 'self' {protocol}://{host_without_port} https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com https://router.project-osrm.org https://viacep.com.br https://brasilapi.com.br https://www.gstatic.com; "
            f"worker-src 'self' {protocol}://{host_without_port} blob:; "
            f"manifest-src 'self' {protocol}://{host_without_port}; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'; "
            f"media-src 'self' {protocol}://{host_without_port}"
        )
        response['Content-Security-Policy'] = csp
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "fullscreen=(self), "
            "sync-xhr=()"
        )
        response['Permissions-Policy'] = permissions_policy
        
        # Strict-Transport-Security (apenas em HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Cache-Control para arquivos sensíveis
        if request.path.startswith('/admin/') or request.path.startswith('/rm/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Log de headers de segurança apenas em desenvolvimento
        if settings.DEBUG and hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(
                f"Headers de segurança aplicados para {request.user.username}",
                extra={
                    'user_id': request.user.id,
                    'path': request.path,
                    'ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100]
                }
            )
        
        return response
