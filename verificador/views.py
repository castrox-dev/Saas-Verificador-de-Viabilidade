"""
Views API para o verificador Django
Substitui os endpoints Flask
"""
import os
import logging
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings

from core.models import Company, CTOMapFile
from .services import VerificadorService
from .geocoding import GeocodingService
from .file_readers import FileReaderService

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health_check(request):
    """Verifica se o serviço está online"""
    return JsonResponse({
        'status': 'online',
        'service': 'Django Verificador'
    })


@login_required
@require_http_methods(["POST"])
def verificar_arquivo(request, company_slug):
    """
    Verifica viabilidade de um arquivo CTO
    Substitui o endpoint Flask /api/verificar
    """
    try:
        company = Company.objects.get(slug=company_slug)
        
        # Verificar acesso
        if not request.user.is_rm_admin and not request.user.is_superuser:
            if not request.user.company or request.user.company != company:
                return JsonResponse({'success': False, 'error': 'Acesso negado'}, status=403)
        
        user = request.user
        
        # Obter arquivo da requisição
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            file_type = os.path.splitext(uploaded_file.name)[1][1:].lower()
            
            # Salvar arquivo temporariamente
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_verificacao')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            with open(temp_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # Verificar arquivo
            result = VerificadorService.verificar_arquivo(temp_path, file_type)
            
            # Limpar arquivo temporário
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")
            
            if result.get('success'):
                # Gerar ID único para a análise
                analysis_id = str(uuid.uuid4())
                
                return JsonResponse({
                    'success': True,
                    'analysis_id': analysis_id,
                    'status': 'completed',
                    **result
                })
            else:
                return JsonResponse(result, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Arquivo não fornecido'
            }, status=400)
            
    except Company.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Empresa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro na verificação: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def verificar_viabilidade(request, company_slug):
    """
    Verifica viabilidade de coordenadas específicas
    Substitui o endpoint Flask /api/verificar-viabilidade
    """
    try:
        company = Company.objects.get(slug=company_slug)
        
        # Verificar acesso
        if not request.user.is_rm_admin and not request.user.is_superuser:
            if not request.user.company or request.user.company != company:
                return JsonResponse({'erro': 'Acesso negado'}, status=403)
        
        user = request.user
        
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        if not lat or not lon:
            return JsonResponse({
                'erro': 'Coordenadas não fornecidas'
            }, status=400)
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({
                'erro': 'Coordenadas inválidas'
            }, status=400)
        
        # Verificar viabilidade
        resultado = VerificadorService.verificar_viabilidade_coordenada(lat, lon, company)
        
        if 'erro' in resultado:
            return JsonResponse(resultado, status=400 if 'não encontrado' in resultado['erro'] else 404)
        
        return JsonResponse(resultado)
        
    except Company.DoesNotExist:
        return JsonResponse({
            'erro': 'Empresa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro na verificação de viabilidade: {e}")
        return JsonResponse({
            'erro': f'Erro interno: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def listar_arquivos(request, company_slug):
    """
    Lista todos os arquivos disponíveis da empresa
    Substitui o endpoint Flask /api/arquivos
    """
    try:
        company = Company.objects.get(slug=company_slug)
        
        # Verificar acesso
        if not request.user.is_rm_admin and not request.user.is_superuser:
            if not request.user.company or request.user.company != company:
                return JsonResponse({'erro': 'Acesso negado'}, status=403)
        
        user = request.user
        
        # Buscar mapas da empresa
        mapas = CTOMapFile.objects.filter(company=company)
        
        arquivos = []
        for mapa in mapas:
            if mapa.file:
                arquivos.append({
                    'id': mapa.id,
                    'nome': mapa.file_name,
                    'tipo': mapa.file_type,
                    'description': mapa.description,
                    'uploaded_at': mapa.uploaded_at.isoformat() if mapa.uploaded_at else None,
                    'is_processed': mapa.is_processed,
                    'viability_score': mapa.viability_score
                })
        
        return JsonResponse(arquivos, safe=False)
        
    except Company.DoesNotExist:
        return JsonResponse({
            'erro': 'Empresa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        return JsonResponse({
            'erro': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def obter_coordenadas(request, company_slug):
    """
    Obtém coordenadas de um arquivo específico
    Substitui o endpoint Flask /api/coordenadas
    """
    try:
        company = Company.objects.get(slug=company_slug)
        
        # Verificar acesso
        if not request.user.is_rm_admin and not request.user.is_superuser:
            if not request.user.company or request.user.company != company:
                return JsonResponse({'erro': 'Acesso negado'}, status=403)
        
        user = request.user
        
        mapa_id = request.GET.get('mapa_id')
        arquivo = request.GET.get('arquivo')
        
        if mapa_id:
            mapa = CTOMapFile.objects.get(id=mapa_id, company=company)
            if mapa.file and hasattr(mapa.file, 'path'):
                coords = FileReaderService.ler_arquivo(mapa.file.path)
                return JsonResponse(coords, safe=False)
            else:
                return JsonResponse({
                    'erro': 'Arquivo não encontrado no sistema'
                }, status=404)
        elif arquivo:
            # Buscar por nome de arquivo
            mapa = CTOMapFile.objects.filter(
                company=company,
                file__icontains=arquivo
            ).first()
            
            if mapa and mapa.file and hasattr(mapa.file, 'path'):
                coords = FileReaderService.ler_arquivo(mapa.file.path)
                return JsonResponse(coords, safe=False)
            else:
                return JsonResponse({
                    'erro': 'Arquivo não encontrado'
                }, status=404)
        else:
            return JsonResponse({
                'erro': 'Parâmetro mapa_id ou arquivo não fornecido'
            }, status=400)
            
    except CTOMapFile.DoesNotExist:
        return JsonResponse({
            'erro': 'Mapa não encontrado'
        }, status=404)
    except Company.DoesNotExist:
        return JsonResponse({
            'erro': 'Empresa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro ao obter coordenadas: {e}")
        return JsonResponse({
            'erro': str(e)
        }, status=500)


@require_http_methods(["GET"])
def geocode(request):
    """
    Geocodificação usando OpenStreetMap Nominatim
    Substitui o endpoint Flask /api/geocode
    """
    endereco = request.GET.get('endereco')
    
    if not endereco:
        return JsonResponse({
            'erro': 'Endereço não especificado'
        }, status=400)
    
    resultado = GeocodingService.geocodificar(endereco)
    
    if resultado:
        return JsonResponse(resultado)
    else:
        return JsonResponse({
            'erro': 'Endereço não encontrado'
        }, status=404)
