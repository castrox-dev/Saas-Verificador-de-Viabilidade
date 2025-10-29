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
from django.shortcuts import get_object_or_404, render
from django.conf import settings

from core.models import Company, CTOMapFile
from core.permissions import company_access_required
from .services import VerificadorService
from .geocoding import GeocodingService
from .file_readers import FileReaderService
from .utils import get_all_ctos, get_arquivo_caminho, classificar_viabilidade
from .models import GeocodingCache, ViabilidadeCache

logger = logging.getLogger(__name__)


@login_required
@company_access_required(require_admin=False)
def verificador_view(request, company_slug):
    """View principal do verificador - página com mapa interativo"""
    company = get_object_or_404(Company, slug=company_slug)
    
    context = {
        'company': company,
    }
    return render(request, 'verificador/verificador.html', context)


@login_required
@company_access_required(require_admin=False)
def verificador_mapa_view(request, company_slug):
    """View do verificador com mapa completo - interface avançada"""
    company = get_object_or_404(Company, slug=company_slug)
    
    context = {
        'company': company,
    }
    return render(request, 'verificador/index.html', context)


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
            
            # Salvar arquivo temporariamente usando context manager
            import tempfile
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_verificacao')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Usar try/finally para garantir limpeza mesmo em caso de erro
            try:
                with open(temp_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                
                # Verificar arquivo
                result = VerificadorService.verificar_arquivo(temp_path, file_type)
            finally:
                # Sempre limpar arquivo temporário
                try:
                    if os.path.exists(temp_path):
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
        mapas = CTOMapFile.objects.filter(company=company, is_processed=True)
        
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


@require_http_methods(["GET"])
def api_arquivos_ftth(request):
    """Lista todos os arquivos disponíveis (KML, KMZ, CSV, XLS, XLSX)"""
    arquivos = []
    
    # Mapeamento de extensões para diretórios
    tipos_map = {
        '.kml': ('kml', getattr(settings, 'FTTH_KML_DIR', None)),
        '.kmz': ('kmz', getattr(settings, 'FTTH_KMZ_DIR', None)),
        '.csv': ('csv', getattr(settings, 'FTTH_CSV_DIR', None)),
        '.xls': ('xls', getattr(settings, 'FTTH_XLS_DIR', None)),
        '.xlsx': ('xlsx', getattr(settings, 'FTTH_XLSX_DIR', None)),
    }
    
    for ext, (tipo, diretorio) in tipos_map.items():
        if diretorio and os.path.exists(diretorio):
            for arquivo in os.listdir(diretorio):
                if arquivo.lower().endswith(ext):
                    arquivos.append({
                        'nome': arquivo,
                        'tipo': tipo,
                        'caminho': os.path.join(diretorio, arquivo)
                    })
    
    return JsonResponse(arquivos, safe=False)


@require_http_methods(["GET"])
def api_coordenadas_ftth(request):
    """Retorna coordenadas de um arquivo específico"""
    arquivo = request.GET.get('arquivo')
    if not arquivo:
        return JsonResponse({'erro': 'Arquivo não especificado'}, status=400)
    
    caminho = get_arquivo_caminho(arquivo)
    if not caminho or not os.path.exists(caminho):
        return JsonResponse({'erro': 'Arquivo não encontrado'}, status=404)
    
    ext = os.path.splitext(arquivo)[1].lower()
    
    try:
        if ext == '.kml':
            coords = FileReaderService.ler_kml(caminho)
        elif ext == '.kmz':
            coords = FileReaderService.ler_kmz(caminho)
        elif ext == '.csv':
            coords = FileReaderService.ler_csv(caminho)
        elif ext in ['.xls', '.xlsx']:
            coords = FileReaderService.ler_excel(caminho)
        else:
            return JsonResponse({'erro': 'Tipo de arquivo não suportado'}, status=400)
        
        return JsonResponse(coords, safe=False)
    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def api_contar_pontos(request):
    """Conta o número de pontos em um arquivo"""
    arquivo = request.GET.get('arquivo')
    if not arquivo:
        return JsonResponse({'erro': 'Arquivo não especificado'}, status=400)
    
    caminho = get_arquivo_caminho(arquivo)
    if not caminho or not os.path.exists(caminho):
        return JsonResponse({'erro': 'Arquivo não encontrado'}, status=404)
    
    ext = os.path.splitext(arquivo)[1].lower()
    
    try:
        if ext == '.kml':
            coords = FileReaderService.ler_kml(caminho)
        elif ext == '.kmz':
            coords = FileReaderService.ler_kmz(caminho)
        elif ext == '.csv':
            coords = FileReaderService.ler_csv(caminho)
        elif ext in ['.xls', '.xlsx']:
            coords = FileReaderService.ler_excel(caminho)
        else:
            return JsonResponse({'erro': 'Tipo de arquivo não suportado'}, status=400)
        
        total_pontos = 0
        for item in coords:
            if item.get('tipo') == 'point':
                total_pontos += 1
            elif item.get('tipo') == 'line':
                total_pontos += len(item.get('coordenadas', []))
        
        return JsonResponse({'total': total_pontos})
    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def api_verificar_viabilidade_ftth(request):
    """Verifica viabilidade de instalação FTTH"""
    try:
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")
        
        if lat is None or lon is None:
            return JsonResponse({"erro": "Coordenadas não fornecidas"}, status=400)
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({"erro": "Coordenadas inválidas"}, status=400)
        
        # Verificar cache de viabilidade
        try:
            cache_obj = ViabilidadeCache.objects.get(lat=lat, lon=lon)
            return JsonResponse(cache_obj.resultado)
        except ViabilidadeCache.DoesNotExist:
            pass
        
        # Buscar CTOs
        ctos = get_all_ctos()
        if not ctos:
            return JsonResponse({"erro": "Nenhum CTO encontrado"}, status=404)
        
        # Fase 1: Filtrar por distância euclidiana
        from .routing import RoutingService
        ctos_com_distancia = []
        for cto in ctos:
            try:
                cto_lat = float(cto["lat"])
                cto_lon = float(cto["lng"])
                distancia_euclidiana = RoutingService.calcular_distancia(lat, lon, cto_lat, cto_lon)
                ctos_com_distancia.append({
                    **cto,
                    "distancia_euclidiana": distancia_euclidiana
                })
            except (ValueError, TypeError, KeyError):
                continue
        
        if not ctos_com_distancia:
            return JsonResponse({"erro": "Nenhum CTO válido encontrado"}, status=404)
        
        # Ordenar e pegar os 5 melhores candidatos
        ctos_com_distancia.sort(key=lambda x: x["distancia_euclidiana"])
        num_candidatos = min(5, len(ctos_com_distancia))
        ctos_candidatos = ctos_com_distancia[:num_candidatos]
        
        # Fase 2: Calcular rota real para os candidatos (PARALELO)
        from .utils import calcular_rota_ruas_single
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        cto_mais_proximo = None
        menor_distancia = float('inf')
        melhor_geometria = None
        
        tarefas = []
        for cto in ctos_candidatos:
            try:
                cto_lat = float(cto["lat"])
                cto_lon = float(cto["lng"])
                tarefas.append((lat, lon, cto_lat, cto_lon, cto))
            except (ValueError, TypeError, KeyError):
                continue
        
        # Executar cálculos em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(calcular_rota_ruas_single, tarefa[0], tarefa[1], tarefa[2], tarefa[3], tarefa[4]): i 
                for i, tarefa in enumerate(tarefas)
            }
            
            for future in as_completed(futures):
                try:
                    distancia_ruas, geometria, cto = future.result()
                    if distancia_ruas < menor_distancia:
                        menor_distancia = distancia_ruas
                        cto_mais_proximo = cto
                        melhor_geometria = geometria
                except Exception as e:
                    print(f"Erro no processamento paralelo: {e}")
                    continue
        
        if not cto_mais_proximo:
            return JsonResponse({"erro": "Nenhum CTO válido encontrado"}, status=404)
        
        # Classificar viabilidade
        viabilidade = classificar_viabilidade(menor_distancia)
        
        # Preparar resposta
        resultado = {
            "viabilidade": viabilidade,
            "cto": {
                "nome": cto_mais_proximo.get("nome", "CTO"),
                "lat": float(cto_mais_proximo["lat"]),
                "lon": float(cto_mais_proximo["lng"]),
                "arquivo": cto_mais_proximo.get("arquivo", "")
            },
            "distancia": {
                "metros": round(menor_distancia, 2),
                "km": round(menor_distancia / 1000, 3)
            },
            "rota": {
                "geometria": melhor_geometria
            }
        }
        
        # Salvar no cache
        ViabilidadeCache.objects.update_or_create(
            lat=lat,
            lon=lon,
            defaults={'resultado': resultado}
        )
        
        return JsonResponse(resultado)
        
    except Exception as e:
        import traceback
        print(f"Erro na verificação de viabilidade: {e}")
        print(f"Traceback completo: {traceback.format_exc()}")
        return JsonResponse({"erro": f"Erro interno do servidor: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def api_cache_geocoding_stats(request):
    """Retorna estatísticas do cache de geocodificação"""
    from django.utils import timezone
    from datetime import timedelta
    
    ttl = timedelta(hours=24)
    agora = timezone.now()
    
    total_entries = GeocodingCache.objects.count()
    valid_entries = GeocodingCache.objects.filter(updated_at__gte=agora - ttl).count()
    expired_entries = total_entries - valid_entries
    
    return JsonResponse({
        'total_entries': total_entries,
        'valid_entries': valid_entries,
        'expired_entries': expired_entries,
        'cache_ttl_hours': 24,
        'max_size': 1000
    })


@require_http_methods(["POST"])
def api_cache_geocoding_clear(request):
    """Limpa o cache de geocodificação"""
    count = GeocodingCache.objects.count()
    GeocodingCache.objects.all().delete()
    return JsonResponse({'mensagem': f'Cache de geocodificação limpo ({count} entradas removidas)'})
