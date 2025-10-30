"""
Views Django para FTTH Viewer
"""
import os
import requests
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib.auth.decorators import login_required

from .utils import (
    ler_kml, ler_kmz, ler_csv, ler_excel, filtrar_coordenadas_brasil,
    calcular_distancia, calcular_rota_ruas_single, classificar_viabilidade,
    get_all_ctos, get_arquivo_caminho, get_cached_geocoding, set_cached_geocoding
)
from .models import ViabilidadeCache


@login_required
def index(request, company_slug):
    """Página principal do FTTH Viewer"""
    return render(request, 'ftth_viewer/index.html')


@login_required
@require_http_methods(["GET"])
def api_arquivos(request, company_slug):
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


@login_required
@require_http_methods(["GET"])
def api_coordenadas(request, company_slug):
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
            coords = ler_kml(caminho)
        elif ext == '.kmz':
            coords = ler_kmz(caminho)
        elif ext == '.csv':
            coords = ler_csv(caminho)
        elif ext in ['.xls', '.xlsx']:
            coords = ler_excel(caminho)
        else:
            return JsonResponse({'erro': 'Tipo de arquivo não suportado'}, status=400)
        
        return JsonResponse(coords, safe=False)
    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_contar_pontos(request, company_slug):
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
            coords = ler_kml(caminho)
        elif ext == '.kmz':
            coords = ler_kmz(caminho)
        elif ext == '.csv':
            coords = ler_csv(caminho)
        elif ext in ['.xls', '.xlsx']:
            coords = ler_excel(caminho)
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


@login_required
@require_http_methods(["GET"])
def api_geocode(request, company_slug):
    """Geocodificação usando OpenStreetMap Nominatim com cache"""
    endereco = request.GET.get('endereco')
    if not endereco:
        return JsonResponse({'erro': 'Endereço não especificado'}, status=400)
    
    # Verificar cache primeiro
    cached_result = get_cached_geocoding(endereco)
    if cached_result:
        return JsonResponse(cached_result)
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': endereco,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'br'
        }
        headers = {'User-Agent': 'FTTH-Viewer-Django/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data:
            resultado = data[0]
            geocoding_result = {
                'lat': float(resultado['lat']),
                'lng': float(resultado['lon']),
                'endereco_completo': resultado['display_name']
            }
            # Armazenar no cache
            set_cached_geocoding(endereco, geocoding_result)
            return JsonResponse(geocoding_result)
        else:
            return JsonResponse({'erro': 'Endereço não encontrado'}, status=404)
            
    except Exception as e:
        return JsonResponse({'erro': f'Erro na geocodificação: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_verificar_viabilidade(request, company_slug):
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
        ctos_com_distancia = []
        for cto in ctos:
            try:
                cto_lat = float(cto["lat"])
                cto_lon = float(cto["lng"])
                distancia_euclidiana = calcular_distancia(lat, lon, cto_lat, cto_lon)
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


@login_required
@require_http_methods(["GET"])
def api_cache_geocoding_stats(request, company_slug):
    """Retorna estatísticas do cache de geocodificação"""
    from .models import GeocodingCache
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


@login_required
@require_http_methods(["POST"])
def api_cache_geocoding_clear(request, company_slug):
    """Limpa o cache de geocodificação"""
    from .models import GeocodingCache
    count = GeocodingCache.objects.count()
    GeocodingCache.objects.all().delete()
    return JsonResponse({'mensagem': f'Cache de geocodificação limpo ({count} entradas removidas)'})

