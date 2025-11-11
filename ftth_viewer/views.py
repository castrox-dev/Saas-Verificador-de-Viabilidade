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
from django.views.decorators.csrf import ensure_csrf_cookie

from .utils import (
    ler_kml, ler_kmz, ler_csv, ler_excel, filtrar_coordenadas_brasil,
    calcular_distancia, calcular_rota_ruas_single, classificar_viabilidade,
    get_all_ctos, get_arquivo_caminho, get_cached_geocoding, set_cached_geocoding,
    remover_cto_do_mapa
)
from .models import ViabilidadeCache
from core.models import CTOMapFile, Company


@login_required
def index(request, company_slug=None):
    """Página principal do FTTH Viewer"""
    context = {
        'company_slug': company_slug,
    }
    return render(request, 'ftth_viewer/index.html', context)


@login_required
@require_http_methods(["GET"])
def api_arquivos(request, company_slug=None):
    """Lista todos os arquivos disponíveis apenas do banco de dados (enviados via upload)"""
    user = request.user
    
    # Permitir bypass do cache com parâmetro refresh
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    # Cache baseado no usuário e empresa
    cache_key = f'api_arquivos_{user.id}_{company_slug or (user.company.slug if user.company else "none")}'
    
    if not force_refresh:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return JsonResponse(cached_result, safe=False)
    
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
                    company = Company.objects.only('id', 'name', 'slug').get(slug=target_company_slug)
                    maps = CTOMapFile.objects.filter(company=company).select_related('company').order_by('-uploaded_at')
                except Company.DoesNotExist:
                    maps = CTOMapFile.objects.none()
            else:
                # RM Admin sem company_slug específico: retornar apenas mapas da empresa do usuário (se tiver)
                # OU retornar erro se não tiver empresa associada
                if user.company:
                    maps = CTOMapFile.objects.filter(company=user.company).select_related('company').order_by('-uploaded_at')
                else:
                    # RM Admin sem empresa: não retornar mapas (precisa especificar empresa)
                    maps = CTOMapFile.objects.none()
        else:
            if not user.company:
                return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
            maps = CTOMapFile.objects.filter(company=user.company).select_related('company').order_by('-uploaded_at')
        
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
        # Se houver erro ao acessar o banco, logar mas não buscar de pastas antigas
        print(f"Erro ao acessar banco de dados: {e}")
        # Não buscar mais de pastas antigas - apenas do banco de dados
    
    # Cachear resultado por 2 minutos
    result = arquivos
    cache.set(cache_key, result, 120)
    
    return JsonResponse(result, safe=False)


@login_required
@require_http_methods(["GET"])
def api_coordenadas(request, company_slug=None):
    """Retorna coordenadas de um arquivo específico apenas do banco de dados"""
    arquivo_nome = request.GET.get('arquivo')
    map_id = request.GET.get('id')  # ID do mapa no banco de dados
    
    if not arquivo_nome and not map_id:
        return JsonResponse({'erro': 'Arquivo não especificado'}, status=400)
    
    # Cache de coordenadas (arquivos não mudam frequentemente)
    cache_key = f'api_coordenadas_{map_id or arquivo_nome}_{company_slug or "none"}'
    cached_coords = cache.get(cache_key)
    if cached_coords is not None:
        return JsonResponse(cached_coords, safe=False)
    
    user = request.user
    caminho = None
    ext = None
    
    # Determinar empresa - SEMPRE exigir empresa
    target_company = None
    if company_slug:
        try:
            target_company = Company.objects.get(slug=company_slug, is_active=True)
        except Company.DoesNotExist:
            return JsonResponse({'erro': 'Empresa não encontrada'}, status=404)
    elif user.is_authenticated:
        # Para usuários normais, SEMPRE usar a empresa deles
        if not user.is_rm_admin and not user.is_superuser:
            if not user.company:
                return JsonResponse({'erro': 'Usuário não está associado a uma empresa'}, status=403)
            target_company = user.company
        # RM Admins: se não tiver company_slug, usar empresa do usuário se existir
        elif user.company:
            target_company = user.company
        else:
            return JsonResponse({'erro': 'É necessário especificar a empresa'}, status=400)
    else:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)
    
    if not target_company:
        return JsonResponse({'erro': 'Empresa não especificada'}, status=400)
    
    # Buscar do banco de dados - SEMPRE filtrar por empresa
    try:
        if map_id:
            # Buscar por ID (preferencial) - SEMPRE verificar se pertence à empresa
            try:
                mapa = CTOMapFile.objects.get(id=map_id, company=target_company)
            except CTOMapFile.DoesNotExist:
                return JsonResponse({'erro': 'Arquivo não encontrado ou não pertence à empresa'}, status=404)
            
            caminho = mapa.file.path if hasattr(mapa.file, 'path') else None
            # Verificar permissões adicionais (RM Admins podem ver, mas ainda precisa filtrar por empresa)
            if not user.is_rm_admin and not user.is_superuser:
                if not user.company or user.company != mapa.company:
                    return JsonResponse({'erro': 'Acesso negado ao arquivo'}, status=403)
        elif arquivo_nome:
            # Buscar por nome do arquivo - SEMPRE filtrar por empresa
            mapa = CTOMapFile.objects.filter(
                company=target_company,
                file__icontains=arquivo_nome
            ).first()
            
            if not mapa:
                return JsonResponse({'erro': 'Arquivo não encontrado na empresa especificada'}, status=404)
            
            if mapa and mapa.file:
                caminho = mapa.file.path if hasattr(mapa.file, 'path') else None
                # Verificar permissões adicionais
                if not user.is_rm_admin and not user.is_superuser:
                    if not user.company or user.company != mapa.company:
                        return JsonResponse({'erro': 'Acesso negado ao arquivo'}, status=403)
    except CTOMapFile.DoesNotExist:
        pass
    except Exception as e:
        print(f"Erro ao buscar arquivo no banco: {e}")
    
    # Não buscar mais de pastas antigas - apenas do banco de dados
    if not caminho or not os.path.exists(caminho):
        return JsonResponse({'erro': 'Arquivo não encontrado no banco de dados'}, status=404)
    
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
        
        # Cachear coordenadas por 1 hora (arquivos não mudam frequentemente)
        cache.set(cache_key, coords, 3600)
        
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
    """Geocodificação direta (endereço -> coordenadas) e reversa (coordenadas -> endereço) usando OpenStreetMap Nominatim com cache"""
    endereco = request.GET.get('endereco')
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    # Geocodificação reversa (coordenadas -> endereço)
    if lat and lon:
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            
            # Verificar cache primeiro (usar coordenadas como chave)
            cache_key = f"{lat_float:.6f},{lon_float:.6f}"
            cached_result = get_cached_geocoding(cache_key)
            if cached_result:
                return JsonResponse(cached_result)
            
            # Fazer geocodificação reversa via Nominatim
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat_float,
                'lon': lon_float,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'pt-BR,pt,en'
            }
            headers = {'User-Agent': 'FTTH-Viewer-Django/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and 'display_name' in data:
                geocoding_result = {
                    'lat': lat_float,
                    'lng': lon_float,
                    'endereco_completo': data['display_name']
                }
                # Armazenar no cache usando coordenadas como chave
                set_cached_geocoding(cache_key, geocoding_result)
                return JsonResponse(geocoding_result)
            else:
                return JsonResponse({'erro': 'Endereço não encontrado para estas coordenadas'}, status=404)
                
        except ValueError:
            return JsonResponse({'erro': 'Coordenadas inválidas'}, status=400)
        except Exception as e:
            return JsonResponse({'erro': f'Erro na geocodificação reversa: {str(e)}'}, status=500)
    
    # Geocodificação direta (endereço -> coordenadas)
    if not endereco:
        return JsonResponse({'erro': 'Endereço ou coordenadas não especificados'}, status=400)
    
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
        
        # Determinar empresa ANTES de verificar cache (para cache separado por empresa)
        company = None
        user = request.user
        
        # Se company_slug foi fornecido, usar ele (prioridade)
        if company_slug:
            try:
                company = Company.objects.get(slug=company_slug, is_active=True)
            except Company.DoesNotExist:
                return JsonResponse({"erro": "Empresa não encontrada"}, status=404)
        elif user.is_authenticated:
            # Para usuários normais, SEMPRE usar a empresa deles
            if not user.is_rm_admin and not user.is_superuser:
                if not user.company:
                    return JsonResponse({"erro": "Usuário não está associado a uma empresa"}, status=403)
                company = user.company
            # RM Admins e superusers: se não tiver company_slug, usar empresa do usuário se existir
            elif user.company:
                company = user.company
            # Se RM Admin não tem empresa e não forneceu slug, não pode verificar sem especificar empresa
            else:
                return JsonResponse({"erro": "É necessário especificar a empresa para verificação"}, status=400)
        else:
            return JsonResponse({"erro": "Usuário não autenticado"}, status=401)
        
        if not company:
            return JsonResponse({"erro": "Empresa não especificada"}, status=400)
        
        # Verificar cache de viabilidade - SEMPRE incluir empresa no cache
        try:
            cache_obj = ViabilidadeCache.objects.get(lat=lat, lon=lon, company=company)
            return JsonResponse(cache_obj.resultado)
        except ViabilidadeCache.DoesNotExist:
            pass
        
        # Company já foi determinado acima (antes de verificar cache)
        
        # Buscar CTOs APENAS da empresa especificada
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
                "arquivo": cto_mais_proximo.get("arquivo", ""),
                "map_id": cto_mais_proximo.get("map_id")
            },
            "distancia": {
                "metros": round(menor_distancia, 2),
                "km": round(menor_distancia / 1000, 3)
            },
            "rota": {
                "geometria": melhor_geometria
            }
        }
        
        # Salvar no cache - SEMPRE incluir empresa para separar caches
        ViabilidadeCache.objects.update_or_create(
            lat=lat,
            lon=lon,
            company=company,  # Incluir empresa no cache
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


@ensure_csrf_cookie
@require_http_methods(["POST"])
def api_adicionar_cto(request, company_slug=None):
    """Adiciona um novo CTO a um mapa existente - apenas para COMPANY_ADMIN e RM"""
    from .utils import adicionar_cto_ao_mapa
    from django.core.cache import cache
    
    # Verificar autenticação manualmente para retornar JSON em vez de redirecionar
    if not request.user.is_authenticated:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)
    
    user = request.user
    
    # Verificar se é admin da empresa ou RM
    if not (user.is_company_admin or user.is_rm_admin or user.is_superuser):
        return JsonResponse({'erro': 'Apenas administradores podem adicionar CTOs'}, status=403)
    
    # Obter dados do POST
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        nome_cto = data.get('nome_cto', '').strip()
        lat = data.get('lat')
        lon = data.get('lon')
        map_id = data.get('map_id')
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    
    # Validar dados
    if not nome_cto:
        return JsonResponse({'erro': 'Nome do CTO é obrigatório'}, status=400)
    
    if lat is None or lon is None:
        return JsonResponse({'erro': 'Coordenadas são obrigatórias'}, status=400)
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Coordenadas inválidas'}, status=400)
    
    if not map_id:
        return JsonResponse({'erro': 'ID do mapa é obrigatório'}, status=400)
    
    # Buscar mapa
    try:
        mapa = CTOMapFile.objects.get(id=map_id)
    except CTOMapFile.DoesNotExist:
        return JsonResponse({'erro': 'Mapa não encontrado'}, status=404)
    
    # Verificar se o usuário tem acesso ao mapa
    if not user.is_rm_admin and not user.is_superuser:
        if not user.company or user.company != mapa.company:
            return JsonResponse({'erro': 'Acesso negado ao mapa'}, status=403)
    
    # Verificar se o arquivo existe
    if not mapa.file or not hasattr(mapa.file, 'path'):
        return JsonResponse({'erro': 'Arquivo do mapa não encontrado'}, status=404)
    
    caminho_arquivo = mapa.file.path
    if not os.path.exists(caminho_arquivo):
        return JsonResponse({'erro': 'Arquivo do mapa não existe no sistema de arquivos'}, status=404)
    
    # Adicionar CTO ao arquivo
    try:
        sucesso = adicionar_cto_ao_mapa(
            caminho_arquivo,
            nome_cto,
            lat,
            lon,
            file_type=mapa.file_type
        )
        
        if not sucesso:
            return JsonResponse({'erro': 'Erro ao adicionar CTO ao arquivo'}, status=500)
        
        # Invalidar caches relacionados
        cache_keys_to_delete = [
            f'api_arquivos_{user.id}_{company_slug or (user.company.slug if user.company else "none")}',
            f'api_coordenadas_{map_id}_{company_slug or "none"}',
        ]
        cache.delete_many(cache_keys_to_delete)
        
        # Atualizar contador de coordenadas do mapa (opcional)
        # Isso pode ser feito em background ou na próxima leitura
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': f'CTO "{nome_cto}" adicionado com sucesso ao mapa',
            'cto': {
                'nome': nome_cto,
                'lat': lat,
                'lon': lon
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Erro ao adicionar CTO: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'erro': f'Erro interno: {str(e)}'}, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def api_remover_cto(request, company_slug=None):
    """Remove um CTO existente de um arquivo de mapa - apenas para COMPANY_ADMIN e RM"""
    from django.core.cache import cache

    if not request.user.is_authenticated:
        return JsonResponse({'erro': 'Usuário não autenticado'}, status=401)

    user = request.user

    if not (user.is_company_admin or user.is_rm_admin or user.is_superuser):
        return JsonResponse({'erro': 'Apenas administradores podem remover CTOs'}, status=403)

    try:
        import json
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)

    map_id = data.get('map_id')
    lat = data.get('lat')
    lon = data.get('lon')
    nome_cto = (data.get('nome_cto') or data.get('nome') or '').strip()

    if not map_id:
        return JsonResponse({'erro': 'ID do mapa é obrigatório'}, status=400)

    if lat is None or lon is None:
        return JsonResponse({'erro': 'Coordenadas são obrigatórias'}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Coordenadas inválidas'}, status=400)

    try:
        mapa = CTOMapFile.objects.get(id=map_id)
    except CTOMapFile.DoesNotExist:
        return JsonResponse({'erro': 'Mapa não encontrado'}, status=404)

    if not user.is_rm_admin and not user.is_superuser:
        if not user.company or user.company != mapa.company:
            return JsonResponse({'erro': 'Acesso negado ao mapa'}, status=403)

    if not mapa.file or not hasattr(mapa.file, 'path'):
        return JsonResponse({'erro': 'Arquivo do mapa não encontrado'}, status=404)

    caminho_arquivo = mapa.file.path
    if not os.path.exists(caminho_arquivo):
        return JsonResponse({'erro': 'Arquivo do mapa não existe no sistema de arquivos'}, status=404)

    try:
        removido = remover_cto_do_mapa(
            caminho_arquivo,
            lat,
            lon,
            nome_cto=nome_cto,
            file_type=mapa.file_type
        )

        if not removido:
            return JsonResponse({'erro': 'CTO não encontrado no arquivo'}, status=404)

        cache_keys_to_delete = [
            f'api_arquivos_{user.id}_{company_slug or (user.company.slug if user.company else "none")}',
            f'api_coordenadas_{map_id}_{company_slug or "none"}',
        ]
        cache.delete_many(cache_keys_to_delete)

        ViabilidadeCache.objects.filter(
            lat=lat,
            lon=lon,
            company=mapa.company
        ).delete()

        return JsonResponse({
            'sucesso': True,
            'mensagem': f'CTO removido com sucesso do mapa "{mapa.file_name}"'
        })

    except Exception as e:
        import traceback
        print(f"Erro ao remover CTO: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'erro': f'Erro interno: {str(e)}'}, status=500)

