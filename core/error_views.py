"""
Views personalizadas para tratamento de erros
"""
from django.shortcuts import render
from django.http import HttpResponseServerError, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
import logging

logger = logging.getLogger(__name__)

def custom_404(request, exception=None):
    """View personalizada para erro 404"""
    try:
        # Forçar uso da página personalizada mesmo em DEBUG
        # Usar context vazio para evitar erros de reverse em URLs
        return render(request, 'errors/404.html', {}, status=404)
    except Exception as e:
        logger.error(f"Erro ao renderizar 404: {str(e)}")
        try:
            return render(request, 'errors/generic.html', status=404)
        except Exception as e2:
            logger.error(f"Erro ao renderizar página genérica: {str(e2)}")
            return HttpResponseNotFound("""
            <html>
            <head><title>404 - Página não encontrada</title></head>
            <body style="margin:0;padding:0;height:100vh;display:flex;align-items:center;justify-content:center;background:#f8f9fa;font-family:Arial,sans-serif;">
                <div style="text-align:center;max-width:500px;padding:2rem;">
                    <h1 style="color:#dc3545;font-size:4rem;margin:0;">404</h1>
                    <h2 style="color:#333;margin:1rem 0;">Página não encontrada</h2>
                    <p style="color:#666;margin:1rem 0;">A página que você está procurando não existe.</p>
                    <a href="/" style="display:inline-block;padding:0.75rem 1.5rem;background:#007bff;color:white;text-decoration:none;border-radius:4px;">Voltar ao início</a>
                </div>
            </body>
            </html>
            """)

def force_404(request):
    """Força 404 para qualquer URL não encontrada"""
    return custom_404(request)

def custom_500(request):
    """View personalizada para erro 500"""
    try:
        return render(request, 'errors/500.html', status=500)
    except Exception as e:
        logger.error(f"Erro ao renderizar 500: {str(e)}")
        try:
            return render(request, 'errors/generic.html', status=500)
        except Exception as e2:
            logger.error(f"Erro ao renderizar página genérica: {str(e2)}")
            return HttpResponseServerError("""
            <html>
            <head><title>500 - Erro interno do servidor</title></head>
            <body>
                <h1>500 - Erro interno do servidor</h1>
                <p>Ocorreu um erro inesperado. Tente novamente mais tarde.</p>
                <a href="/">Voltar ao início</a>
            </body>
            </html>
            """)

def custom_403(request, exception=None):
    """View personalizada para erro 403"""
    try:
        return render(request, 'errors/403.html', status=403)
    except Exception as e:
        logger.error(f"Erro ao renderizar 403: {str(e)}")
        return HttpResponseForbidden("""
        <html>
        <head><title>403 - Acesso negado</title></head>
        <body>
            <h1>403 - Acesso negado</h1>
            <p>Você não tem permissão para acessar esta página.</p>
            <a href="/">Voltar ao início</a>
        </body>
        </html>
        """)

def custom_400(request, exception=None):
    """View personalizada para erro 400"""
    try:
        return render(request, 'errors/400.html', status=400)
    except Exception as e:
        logger.error(f"Erro ao renderizar 400: {str(e)}")
        return HttpResponseBadRequest("""
        <html>
        <head><title>400 - Requisição inválida</title></head>
        <body>
            <h1>400 - Requisição inválida</h1>
            <p>A requisição não pôde ser processada.</p>
            <a href="/">Voltar ao início</a>
        </body>
        </html>
        """)
