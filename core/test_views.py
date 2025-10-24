"""
Views de teste para páginas de erro (apenas em DEBUG)
"""
from django.conf import settings
from django.http import Http404, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied

def test_404(request):
    """Teste da página 404"""
    if not settings.DEBUG:
        raise Http404("Página não encontrada")
    raise Http404("Esta é uma página de teste 404")

def test_500(request):
    """Teste da página 500"""
    if not settings.DEBUG:
        raise Http404("Página não encontrada")
    raise Exception("Esta é uma página de teste 500")

def test_403(request):
    """Teste da página 403"""
    if not settings.DEBUG:
        raise Http404("Página não encontrada")
    raise PermissionDenied("Esta é uma página de teste 403")

def test_400(request):
    """Teste da página 400"""
    if not settings.DEBUG:
        raise Http404("Página não encontrada")
    return HttpResponseBadRequest("Esta é uma página de teste 400")

def force_404(request):
    """Força um 404 para testar a página personalizada"""
    from django.http import Http404
    raise Http404("Página de teste 404 personalizada")

def show_404_page(request):
    """Mostra diretamente a página 404 personalizada"""
    from django.shortcuts import render
    return render(request, 'errors/404.html', status=404)
