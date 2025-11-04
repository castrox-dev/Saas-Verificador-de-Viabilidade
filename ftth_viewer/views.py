"""
Views Django para FTTH Viewer
"""
import os
import requests
from django.shortcuts import render, get_object_or_404
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
from core.models import CTOMapFile, Company


@login_required
def index(request, company_slug=None):
    """Página principal do FTTH Viewer"""
    return render(request, 'ftth_viewer/index.html')


@login_required
@require_http_methods(["GET"])
def api_arquivos(request, company_slug=None):
    """Lista todos os arquivos disponíveis (KML, KMZ, CSV, XLS, XLSX) do banco de dados ou da pasta media/cto_maps"""
    user = request.user
    
    # Determinar empresa a ser listada
    target_company_slug = company_slug
    if not target_company_slug:
        if user.is_rm_admin or user.is_superuser:
            # RM Admin sem company_slug: tentar usar 'fibramar' como padrão
            target_company_slug = getattr(settings, 'DEFAULT_COMPANY_SLUG', 'fibramar')
        else:
            # Usuário normal usa empresa dele
            if not user.company:
                return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
            target_company_slug = user.company.slug
    
    # Verificar permissões
    if not user.is_rm_admin and not user.is_superuser:
        if not user.company:
            return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
        if target_company_slug != user.company.slug:
            return JsonResponse({'erro': 'Acesso negado à empresa'}, status=403)
    
    arquivos = []
    
    # Primeiro, tentar buscar do banco de dados
    try:
        if user.is_rm_admin or user.is_superuser:
            if target_company_slug:
                try:
                    company = Company.objects.get(slug=target_company_slug)
                    maps = CTOMapFile.objects.filter(company=company).select_related('company').order_by('-uploaded_at')
                except Company.DoesNotExist:
                    maps = CTOMapFile.objects.none()
            else:
                maps = CTOMapFile.objects.all().select_related('company').order_by('company__name', '-uploaded_at')
                # Se for múltiplas empresas, retornar agrupado
                if maps.exists():
                    empresas_map = {}
                    for mapa in maps:
                        empresa_nome = mapa.company.name if mapa.company else 'Sem empresa'
                        if empresa_nome not in empresas_map:
                            empresas_map[empresa_nome] = []
                        empresas_map[empresa_nome].append({
                            'nome': mapa.file_name,
                            'tipo': mapa.file_type,
                            'caminho': mapa.file.path if mapa.file else None,
                            'empresa': empresa_nome,
                            'empresa_slug': mapa.company.slug if mapa.company else None,
                            'id': mapa.id
                        })
                    return JsonResponse({
                        'agrupado': True,
                        'empresas': empresas_map
                    }, safe=False)
        else:
            if not user.company:
                return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
            maps = CTOMapFile.objects.filter(company=user.company).order_by('-uploaded_at')
        
        # Processar arquivos do banco
        for mapa in maps:
            if mapa.file:
                arquivos.append({
                    'nome': mapa.file_name,
                    'tipo': mapa.file_type,
                    'caminho': mapa.file.path if mapa.file else None,
                    'id': mapa.id
                })
    except Exception as e:
        # Se houver erro ao acessar o banco, continuar para buscar da pasta
        print(f"Erro ao acessar banco de dados, buscando da pasta: {e}")
    
    # Se não encontrou no banco, buscar da pasta media/cto_maps
    if not arquivos:
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        company_dir = os.path.join(media_root, 'cto_maps', target_company_slug)
        
        if os.path.exists(company_dir):
            # Buscar arquivos nas subpastas
            subdirs = {
                'kml': 'kml',
                'kmz': 'kmz',
                'csv': 'csv',
                'xls': 'xls',
                'xlsx': 'xlsx'
            }
            
            for ext, subdir in subdirs.items():
                subdir_path = os.path.join(company_dir, subdir)
                if os.path.exists(subdir_path):
                    try:
                        for arquivo in os.listdir(subdir_path):
                            if arquivo.lower().endswith(f'.{ext}'):
                                arquivo_path = os.path.join(subdir_path, arquivo)
                                arquivos.append({
                                    'nome': arquivo,
                                    'tipo': ext,
                                    'caminho': arquivo_path,
                                    'id': None  # Não tem ID do banco
                                })
                    except Exception as e:
                        print(f"Erro ao listar arquivos em {subdir_path}: {e}")
                        continue
            
            # Ordenar por nome
            arquivos.sort(key=lambda x: x['nome'].lower())
    
    return JsonResponse(arquivos, safe=False)


@login_required
@require_http_methods(["GET"])
def api_coordenadas(request, company_slug=None):
    """Retorna coordenadas de um arquivo específico do banco de dados ou da pasta media/cto_maps"""
    arquivo_nome = request.GET.get('arquivo')
    map_id = request.GET.get('id')  # ID do mapa no banco de dados
    
    if not arquivo_nome and not map_id:
        return JsonResponse({'erro': 'Arquivo não especificado'}, status=400)
    
    user = request.user
    caminho = None
    ext = None
    
    # Determinar empresa
    target_company_slug = company_slug
    if not target_company_slug:
        if user.is_rm_admin or user.is_superuser:
            target_company_slug = getattr(settings, 'DEFAULT_COMPANY_SLUG', 'fibramar')
        else:
            if not user.company:
                return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
            target_company_slug = user.company.slug
    
    # Primeiro, tentar buscar do banco de dados
    try:
        if map_id:
            # Buscar por ID (preferencial)
            mapa = CTOMapFile.objects.get(id=map_id)
            caminho = mapa.file.path if hasattr(mapa.file, 'path') else None
            # Verificar permissões
            if not user.is_rm_admin and not user.is_superuser:
                if not user.company or user.company != mapa.company:
                    return JsonResponse({'erro': 'Acesso negado ao arquivo'}, status=403)
        elif arquivo_nome:
            # Buscar por nome do arquivo
            if user.is_rm_admin or user.is_superuser:
                mapa = CTOMapFile.objects.filter(file__icontains=arquivo_nome).first()
            else:
                if not user.company:
                    return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
                mapa = CTOMapFile.objects.filter(
                    company=user.company,
                    file__icontains=arquivo_nome
                ).first()
            
            if mapa and mapa.file:
                caminho = mapa.file.path if hasattr(mapa.file, 'path') else None
                # Verificar permissões
                if not user.is_rm_admin and not user.is_superuser:
                    if not user.company or user.company != mapa.company:
                        return JsonResponse({'erro': 'Acesso negado ao arquivo'}, status=403)
    except CTOMapFile.DoesNotExist:
        pass
    except Exception as e:
        print(f"Erro ao buscar arquivo no banco: {e}")
    
    # Se não encontrou no banco, buscar da pasta
    if not caminho or not os.path.exists(caminho):
        if arquivo_nome:
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            company_dir = os.path.join(media_root, 'cto_maps', target_company_slug)
            
            # Buscar o arquivo nas subpastas
            subdirs = ['kml', 'kmz', 'csv', 'xls', 'xlsx']
            for subdir in subdirs:
                subdir_path = os.path.join(company_dir, subdir)
                if os.path.exists(subdir_path):
                    arquivo_path = os.path.join(subdir_path, arquivo_nome)
                    if os.path.exists(arquivo_path):
                        caminho = arquivo_path
                        ext = subdir  # A extensão é a subpasta
                        break
    
    if not caminho or not os.path.exists(caminho):
        return JsonResponse({'erro': 'Arquivo físico não encontrado'}, status=404)
    
    # Determinar extensão se não foi definida
    if not ext:
        file_name_ext = os.path.splitext(caminho)[1].lower().lstrip('.')
        if file_name_ext:
            ext = file_name_ext
        else:
            # Tentar detectar pelo conteúdo
            try:
                with open(caminho, 'rb') as f:
                    first_bytes = f.read(4)
                    if first_bytes[:2] == b'PK':
                        ext = 'kmz'
                    elif first_bytes.startswith(b'<?') or first_bytes.startswith(b'<'):
                        ext = 'kml'
            except:
                pass
    
    if not ext:
        return JsonResponse({'erro': 'Tipo de arquivo não identificado'}, status=400)
    
    try:
        # Normalizar extensão
        ext = ext.lstrip('.').lower()
        
        if ext == 'kml':
            coords = ler_kml(caminho)
        elif ext == 'kmz':
            coords = ler_kmz(caminho)
        elif ext == 'csv':
            coords = ler_csv(caminho)
        elif ext in ['xls', 'xlsx']:
            coords = ler_excel(caminho)
        else:
            return JsonResponse({'erro': f'Tipo de arquivo não suportado: {ext}'}, status=400)
        
        return JsonResponse(coords, safe=False)
    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_contar_pontos(request, company_slug=None):
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
def api_geocode(request, company_slug=None):
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
def api_verificar_viabilidade(request, company_slug=None):
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
        
        # Determinar empresa para filtrar CTOs
        company = None
        user = request.user
        if company_slug:
            # Buscar empresa pelo slug
            try:
                company = Company.objects.get(slug=company_slug, is_active=True)
            except Company.DoesNotExist:
                pass
        elif user.is_authenticated and user.company:
            # Usar empresa do usuário
            company = user.company
        # Se for RM admin ou superuser, buscar todos os CTOs (company=None)
        
        # Buscar CTOs
        ctos = get_all_ctos(company=company)
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
def api_cache_geocoding_stats(request, company_slug=None):
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
def api_cache_geocoding_clear(request, company_slug=None):
    """Limpa o cache de geocodificação"""
    from .models import GeocodingCache
    count = GeocodingCache.objects.count()
    GeocodingCache.objects.all().delete()
    return JsonResponse({'mensagem': f'Cache de geocodificação limpo ({count} entradas removidas)'})

