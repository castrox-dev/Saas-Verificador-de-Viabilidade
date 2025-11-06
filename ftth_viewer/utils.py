"""
Funções auxiliares para processamento de arquivos KML/KMZ/CSV/XLS e cálculos geográficos
"""
import os
import sys
import json
import xml.etree.ElementTree as ET
import requests
import zipfile
import math
import csv
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.core.cache import cache
from .models import GeocodingCache, ViabilidadeCache


def get_base_path():
    """Retorna o caminho base do projeto"""
    return Path(settings.BASE_DIR)


def ler_kml(caminho_kml):
    """Lê um arquivo KML e extrai coordenadas"""
    try:
        tree = ET.parse(caminho_kml)
        root = tree.getroot()
        
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        coordenadas = []
        
        for placemark in root.findall('.//kml:Placemark', ns):
            nome = placemark.find('.//kml:name', ns)
            nome_texto = nome.text if nome is not None else "Sem nome"
            
            # Buscar coordenadas em Point
            point = placemark.find('.//kml:Point/kml:coordinates', ns)
            if point is not None:
                coords = point.text.strip().split(',')
                if len(coords) >= 2:
                    try:
                        lon, lat = float(coords[0]), float(coords[1])
                        coordenadas.append({
                            'nome': nome_texto,
                            'lat': lat,
                            'lng': lon,
                            'tipo': 'point'
                        })
                    except ValueError:
                        continue
            
            # Buscar coordenadas em LineString
            linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
            if linestring is not None:
                coords_text = linestring.text.strip()
                pontos = []
                for linha in coords_text.split('\n'):
                    linha = linha.strip()
                    if linha:
                        coords = linha.split(',')
                        if len(coords) >= 2:
                            try:
                                lon, lat = float(coords[0]), float(coords[1])
                                pontos.append([lat, lon])
                            except ValueError:
                                continue
                
                if pontos:
                    coordenadas.append({
                        'nome': nome_texto,
                        'coordenadas': pontos,
                        'tipo': 'line'
                    })
        
        return coordenadas
    except Exception as e:
        print(f"Erro ao ler KML {caminho_kml}: {e}")
        return []


def ler_kmz(caminho_kmz, filtrar_brasil=False):
    """Lê um arquivo KMZ e extrai coordenadas"""
    import tempfile
    try:
        with zipfile.ZipFile(caminho_kmz, 'r') as kmz:
            for arquivo in kmz.namelist():
                if arquivo.endswith('.kml'):
                    with kmz.open(arquivo) as kml_file:
                        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.kml') as temp_kml:
                            temp_kml.write(kml_file.read())
                            temp_path = temp_kml.name
                        
                        coordenadas = ler_kml(temp_path)
                        
                        # Remover arquivo temporário
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        if filtrar_brasil:
                            coordenadas = filtrar_coordenadas_brasil(coordenadas)
                        
                        return coordenadas
        return []
    except Exception as e:
        print(f"Erro ao ler KMZ {caminho_kmz}: {e}")
        return []


def filtrar_coordenadas_brasil(coordenadas):
    """Filtra coordenadas que estão dentro do território brasileiro"""
    coordenadas_filtradas = []
    for coord in coordenadas:
        if coord.get('tipo') == 'point':
            lat, lng = coord['lat'], coord['lng']
            if -34 <= lat <= 5 and -74 <= lng <= -32:
                coordenadas_filtradas.append(coord)
        else:
            coordenadas_filtradas.append(coord)
    return coordenadas_filtradas


def ler_csv(caminho_csv):
    """Lê um arquivo CSV e extrai coordenadas"""
    try:
        coordenadas = []
        
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
        
        df = pd.read_csv(caminho_csv, delimiter=delimiter, encoding='utf-8')
        
        lat_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'latitude', 'y'])]
        lng_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'longitude', 'x'])]
        nome_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['nome', 'name', 'id', 'cto'])]
        
        if not lat_cols or not lng_cols:
            numeric_cols = df.select_dtypes(include=[float, int]).columns
            if len(numeric_cols) >= 2:
                lat_col = numeric_cols[0]
                lng_col = numeric_cols[1]
            else:
                return []
        else:
            lat_col = lat_cols[0]
            lng_col = lng_cols[0]
        
        nome_col = nome_cols[0] if nome_cols else None
        
        for index, row in df.iterrows():
            try:
                lat = float(row[lat_col])
                lng = float(row[lng_col])
                nome = str(row[nome_col]) if nome_col and pd.notna(row[nome_col]) else f"Ponto {index + 1}"
                
                coordenadas.append({
                    'nome': nome,
                    'lat': lat,
                    'lng': lng,
                    'tipo': 'point'
                })
            except (ValueError, TypeError):
                continue
        
        return coordenadas
    except Exception as e:
        print(f"Erro ao ler CSV {caminho_csv}: {e}")
        return []


def ler_excel(caminho_excel):
    """Lê um arquivo Excel (XLS ou XLSX) e extrai coordenadas"""
    try:
        coordenadas = []
        df = pd.read_excel(caminho_excel)
        
        lat_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'latitude', 'y'])]
        lng_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'longitude', 'x'])]
        nome_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['nome', 'name', 'id', 'cto'])]
        
        if not lat_cols or not lng_cols:
            numeric_cols = df.select_dtypes(include=[float, int]).columns
            if len(numeric_cols) >= 2:
                lat_col = numeric_cols[0]
                lng_col = numeric_cols[1]
            else:
                return []
        else:
            lat_col = lat_cols[0]
            lng_col = lng_cols[0]
        
        nome_col = nome_cols[0] if nome_cols else None
        
        for index, row in df.iterrows():
            try:
                lat = float(row[lat_col])
                lng = float(row[lng_col])
                nome = str(row[nome_col]) if nome_col and pd.notna(row[nome_col]) else f"Ponto {index + 1}"
                
                coordenadas.append({
                    'nome': nome,
                    'lat': lat,
                    'lng': lng,
                    'tipo': 'point'
                })
            except (ValueError, TypeError):
                continue
        
        return coordenadas
    except Exception as e:
        print(f"Erro ao ler Excel {caminho_excel}: {e}")
        return []


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula a distância entre dois pontos usando a fórmula de Haversine (metros)"""
    R = 6371000  # Raio da Terra em metros
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calcular_rota_ruas(lat1, lon1, lat2, lon2):
    """Calcula rota usando OSRM e retorna (distancia_metros, geometria)"""
    try:
        cache_key = f"route_{lat1:.6f},{lon1:.6f}->{lat2:.6f},{lon2:.6f}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        base_url = "https://router.project-osrm.org/route/v1/driving"
        url = f"{base_url}/{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
        params = {
            "overview": "simplified",
            "geometries": "geojson",
            "alternatives": "false",
            "steps": "false"
        }
        headers = {"User-Agent": "FTTH-Viewer-Django/1.0"}
        
        timeout = getattr(settings, 'FTTH_ROUTING_TIMEOUT', 15)
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("routes"):
            route = data["routes"][0]
            distancia = float(route.get("distance", calcular_distancia(lat1, lon1, lat2, lon2)))
            coords = route.get("geometry", {}).get("coordinates") or [[lon1, lat1], [lon2, lat2]]
            result = (distancia, coords)
            cache.set(cache_key, result, 1800)  # Cache por 30 minutos
            return result
    except Exception as e:
        print(f"Erro ao calcular rota OSRM: {e}")
    
    # Fallback para distância euclidiana
    distancia = calcular_distancia(lat1, lon1, lat2, lon2)
    coords = [[lon1, lat1], [lon2, lat2]]
    return distancia, coords


def calcular_rota_ruas_single(lat1, lon1, lat2, lon2, cto_info=None):
    """Versão single-threaded para processamento paralelo"""
    distancia, coords = calcular_rota_ruas(lat1, lon1, lat2, lon2)
    return distancia, coords, cto_info


def classificar_viabilidade(distancia_metros):
    """Classifica a viabilidade baseada na distância"""
    config = getattr(settings, 'FTTH_VIABILIDADE_CONFIG', {
        'viavel': 300,
        'limitada': 800,
        'inviavel': 800
    })
    
    if distancia_metros <= config['viavel']:
        return {
            "status": "Viável",
            "cor": "#28a745",
            "descricao": "Instalação viável"
        }
    elif distancia_metros <= config['limitada']:
        return {
            "status": "Viabilidade Limitada",
            "cor": "#ffc107",
            "descricao": "Instalação com limitações"
        }
    else:
        return {
            "status": "Sem viabilidade",
            "cor": "#dc3545",
            "descricao": "Instalação não viável"
        }


def get_cached_geocoding(endereco):
    """Busca geocodificação no cache"""
    try:
        cache_obj = GeocodingCache.objects.get(endereco=endereco)
        return cache_obj.to_dict()
    except GeocodingCache.DoesNotExist:
        return None


def set_cached_geocoding(endereco, data):
    """Salva geocodificação no cache"""
    GeocodingCache.objects.update_or_create(
        endereco=endereco,
        defaults={
            'lat': data['lat'],
            'lng': data['lng'],
            'endereco_completo': data.get('endereco_completo', '')
        }
    )


def get_all_ctos(company=None):
    """Retorna todos os CTOs apenas dos arquivos enviados via upload (banco de dados)"""
    coords = []
    
    # Primeiro, tentar buscar do banco de dados
    try:
        from core.models import CTOMapFile
        
        # IMPORTANTE: Sempre exigir empresa - nunca retornar todos os arquivos
        if not company:
            # Se não foi fornecida empresa, não retornar nada
            return []
        
        # Filtrar APENAS por empresa específica
        map_files = CTOMapFile.objects.filter(company=company, file__isnull=False)
        
        # Processar cada arquivo do banco
        for map_file in map_files:
            try:
                # Verificar se o arquivo existe fisicamente
                if not map_file.file or not hasattr(map_file.file, 'path'):
                    continue
                
                caminho = map_file.file.path
                if not os.path.exists(caminho):
                    continue
                
                # Determinar extensão
                file_name = map_file.file.name
                ext = os.path.splitext(file_name)[1].lower().lstrip('.')
                
                # Ler coordenadas baseado no tipo
                try:
                    if ext == 'kml':
                        arquivo_coords = ler_kml(caminho)
                    elif ext == 'kmz':
                        arquivo_coords = ler_kmz(caminho)
                    elif ext == 'csv':
                        arquivo_coords = ler_csv(caminho)
                    elif ext in ['xls', 'xlsx']:
                        arquivo_coords = ler_excel(caminho)
                    else:
                        continue
                    
                    # Adicionar informações do arquivo
                    for coord in arquivo_coords:
                        coord["arquivo"] = os.path.basename(file_name)
                        coord["map_id"] = map_file.id
                        coords.append(coord)
                except Exception as e:
                    # Log erro mas continue processando outros arquivos
                    print(f"Erro ao processar arquivo {file_name}: {e}")
                    continue
            except Exception as e:
                # Log erro mas continue processando outros arquivos
                print(f"Erro ao acessar arquivo {map_file.id}: {e}")
                continue
    except Exception as e:
        # Se houver erro ao acessar o banco, logar mas não buscar de pastas antigas
        print(f"Erro ao acessar banco de dados: {e}")
        # Não buscar mais de pastas antigas - apenas do banco de dados
    
    # Não buscar mais de pastas antigas ou diretórios do sistema
    # Apenas usar mapas que foram enviados via upload (banco de dados)
    
    return coords


def get_arquivo_caminho(arquivo):
    """Retorna o caminho completo de um arquivo baseado na extensão"""
    settings_map = {
        '.kml': getattr(settings, 'FTTH_KML_DIR', None),
        '.kmz': getattr(settings, 'FTTH_KMZ_DIR', None),
        '.csv': getattr(settings, 'FTTH_CSV_DIR', None),
        '.xls': getattr(settings, 'FTTH_XLS_DIR', None),
        '.xlsx': getattr(settings, 'FTTH_XLSX_DIR', None),
    }
    
    ext = Path(arquivo).suffix.lower()
    diretorio = settings_map.get(ext)
    
    if diretorio and os.path.exists(diretorio):
        return os.path.join(diretorio, arquivo)
    return None


def adicionar_cto_kml(caminho_kml, nome_cto, lat, lng):
    """Adiciona um CTO a um arquivo KML"""
    try:
        # Ler arquivo existente
        tree = ET.parse(caminho_kml)
        root = tree.getroot()
        
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        # Encontrar ou criar Document
        document = root.find('.//kml:Document', ns)
        if document is None:
            # Se não houver Document, criar um
            document = ET.SubElement(root, '{http://www.opengis.net/kml/2.2}Document')
        
        # Criar novo Placemark
        placemark = ET.SubElement(document, '{http://www.opengis.net/kml/2.2}Placemark')
        
        # Adicionar nome
        name_elem = ET.SubElement(placemark, '{http://www.opengis.net/kml/2.2}name')
        name_elem.text = nome_cto
        
        # Adicionar Point com coordenadas
        point = ET.SubElement(placemark, '{http://www.opengis.net/kml/2.2}Point')
        coords_elem = ET.SubElement(point, '{http://www.opengis.net/kml/2.2}coordinates')
        coords_elem.text = f"{lng:.6f},{lat:.6f},0"
        
        # Salvar arquivo
        tree.write(caminho_kml, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"Erro ao adicionar CTO em KML {caminho_kml}: {e}")
        return False


def adicionar_cto_kmz(caminho_kmz, nome_cto, lat, lng):
    """Adiciona um CTO a um arquivo KMZ"""
    import tempfile
    import shutil
    try:
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp()
        
        # Extrair KMZ
        with zipfile.ZipFile(caminho_kmz, 'r') as kmz:
            kmz.extractall(temp_dir)
        
        # Encontrar arquivo KML dentro do KMZ
        kml_file = None
        for arquivo in os.listdir(temp_dir):
            if arquivo.endswith('.kml'):
                kml_file = os.path.join(temp_dir, arquivo)
                break
        
        if not kml_file:
            # Se não houver KML, criar um novo
            kml_file = os.path.join(temp_dir, 'doc.kml')
            root = ET.Element('{http://www.opengis.net/kml/2.2}kml')
            document = ET.SubElement(root, '{http://www.opengis.net/kml/2.2}Document')
            tree = ET.ElementTree(root)
            tree.write(kml_file, encoding='utf-8', xml_declaration=True)
        
        # Adicionar CTO ao KML
        if not adicionar_cto_kml(kml_file, nome_cto, lat, lng):
            shutil.rmtree(temp_dir)
            return False
        
        # Recriar KMZ
        with zipfile.ZipFile(caminho_kmz, 'w', zipfile.ZIP_DEFLATED) as kmz:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    kmz.write(file_path, arcname)
        
        # Limpar diretório temporário
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        print(f"Erro ao adicionar CTO em KMZ {caminho_kmz}: {e}")
        return False


def adicionar_cto_csv(caminho_csv, nome_cto, lat, lng):
    """Adiciona um CTO a um arquivo CSV"""
    try:
        # Ler CSV existente para detectar delimitador e colunas
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            reader = csv.DictReader(f, delimiter=delimiter)
            fieldnames = reader.fieldnames
        
        # Se não houver colunas de nome, lat, lng, criar padrão
        if not fieldnames:
            fieldnames = ['nome', 'lat', 'lng']
        
        # Garantir que existam colunas necessárias
        if 'nome' not in fieldnames:
            fieldnames.insert(0, 'nome')
        if 'lat' not in fieldnames:
            fieldnames.append('lat')
        if 'lng' not in fieldnames:
            fieldnames.append('lng')
        
        # Ler todos os dados existentes
        f.seek(0)
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)
        
        # Adicionar novo CTO
        new_row = {}
        for field in fieldnames:
            if field == 'nome':
                new_row[field] = nome_cto
            elif field == 'lat':
                new_row[field] = str(lat)
            elif field == 'lng':
                new_row[field] = str(lng)
            else:
                new_row[field] = ''
        
        rows.append(new_row)
        
        # Escrever CSV atualizado
        with open(caminho_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"Erro ao adicionar CTO em CSV {caminho_csv}: {e}")
        return False


def adicionar_cto_excel(caminho_excel, nome_cto, lat, lng):
    """Adiciona um CTO a um arquivo Excel"""
    try:
        # Ler Excel existente
        df = pd.read_excel(caminho_excel)
        
        # Verificar se existem colunas de nome, lat, lng
        nome_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['nome', 'name', 'id', 'cto'])]
        lat_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'latitude', 'y'])]
        lng_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'longitude', 'x'])]
        
        # Se não houver colunas apropriadas, criar novas
        if not nome_cols:
            df['nome'] = ''
        if not lat_cols:
            df['lat'] = None
        if not lng_cols:
            df['lng'] = None
        
        # Usar primeira coluna encontrada ou criar padrão
        nome_col = nome_cols[0] if nome_cols else 'nome'
        lat_col = lat_cols[0] if lat_cols else 'lat'
        lng_col = lng_cols[0] if lng_cols else 'lng'
        
        # Adicionar nova linha
        new_row = df.iloc[0].copy() if len(df) > 0 else pd.Series()
        new_row[nome_col] = nome_cto
        new_row[lat_col] = lat
        new_row[lng_col] = lng
        
        # Adicionar ao DataFrame
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Salvar Excel
        df.to_excel(caminho_excel, index=False)
        return True
    except Exception as e:
        print(f"Erro ao adicionar CTO em Excel {caminho_excel}: {e}")
        return False


def adicionar_cto_ao_mapa(caminho_arquivo, nome_cto, lat, lng, file_type=None):
    """Adiciona um CTO a um arquivo de mapa baseado no tipo"""
    if not file_type:
        ext = os.path.splitext(caminho_arquivo)[1].lower().lstrip('.')
        file_type = ext
    
    file_type = file_type.lower()
    
    if file_type == 'kml':
        return adicionar_cto_kml(caminho_arquivo, nome_cto, lat, lng)
    elif file_type == 'kmz':
        return adicionar_cto_kmz(caminho_arquivo, nome_cto, lat, lng)
    elif file_type == 'csv':
        return adicionar_cto_csv(caminho_arquivo, nome_cto, lat, lng)
    elif file_type in ['xls', 'xlsx']:
        return adicionar_cto_excel(caminho_arquivo, nome_cto, lat, lng)
    else:
        print(f"Tipo de arquivo não suportado para adicionar CTO: {file_type}")
        return False

