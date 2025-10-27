from flask import Flask, jsonify, render_template, request
import os
import sys
import json
import xml.etree.ElementTree as ET
import requests
import zipfile
import webbrowser
import threading
import time
import math
import openrouteservice
import pandas as pd
import csv
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importar configurações
try:
    from config import OPENROUTESERVICE_API_KEY, ROUTING_TIMEOUT, ENABLE_ROUTE_CACHE, MAX_CACHE_SIZE
except ImportError:
    OPENROUTESERVICE_API_KEY = 'YOUR_FREE_OPENROUTESERVICE_KEY'
    ROUTING_TIMEOUT = 15
    ENABLE_ROUTE_CACHE = True
    MAX_CACHE_SIZE = 1000

# ===== CACHE DE GEOCODIFICAÇÃO =====
GEOCODING_CACHE = {}
GEOCODING_CACHE_TTL = 86400  # 24 horas em segundos
GEOCODING_CACHE_FILE = "geocoding_cache.json"
GEOCODING_CACHE_MAX_SIZE = 1000  # Máximo de entradas no cache

def load_geocoding_cache():
    """Carrega o cache de geocodificação do arquivo"""
    global GEOCODING_CACHE
    try:
        if os.path.exists(GEOCODING_CACHE_FILE):
            with open(GEOCODING_CACHE_FILE, 'r', encoding='utf-8') as f:
                GEOCODING_CACHE = json.load(f)
            print(f"Cache de geocodificacao carregado: {len(GEOCODING_CACHE)} entradas")
        else:
            print("Arquivo de cache nao encontrado, iniciando cache vazio")
    except Exception as e:
        print(f"Erro ao carregar cache de geocodificacao: {e}")
        GEOCODING_CACHE = {}

def save_geocoding_cache():
    """Salva o cache de geocodificação no arquivo"""
    try:
        with open(GEOCODING_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(GEOCODING_CACHE, f, ensure_ascii=False, indent=2)
        print(f"Cache de geocodificacao salvo: {len(GEOCODING_CACHE)} entradas")
    except Exception as e:
        print(f"Erro ao salvar cache de geocodificacao: {e}")

def get_cached_geocoding(endereco):
    """Retorna dados de geocodificação do cache se válidos"""
    if endereco in GEOCODING_CACHE:
        cache_entry = GEOCODING_CACHE[endereco]
        current_time = time.time()
        
        # Verificar se o cache ainda é válido
        if current_time - cache_entry['timestamp'] < GEOCODING_CACHE_TTL:
            print(f"Cache HIT para: {endereco}")
            return cache_entry['data']
        else:
            # Cache expirado, remover
            del GEOCODING_CACHE[endereco]
            print(f"Cache expirado para: {endereco}")
    
    print(f"Cache MISS para: {endereco}")
    return None

def set_cached_geocoding(endereco, data):
    """Armazena dados de geocodificação no cache"""
    # Limpar cache se estiver muito grande
    if len(GEOCODING_CACHE) >= GEOCODING_CACHE_MAX_SIZE:
        # Remover entradas mais antigas
        oldest_key = min(GEOCODING_CACHE.keys(), 
                        key=lambda k: GEOCODING_CACHE[k]['timestamp'])
        del GEOCODING_CACHE[oldest_key]
        print(f"Cache limpo, removida entrada mais antiga: {oldest_key}")
    
    # Adicionar nova entrada
    GEOCODING_CACHE[endereco] = {
        'data': data,
        'timestamp': time.time()
    }
    print(f"Cache atualizado para: {endereco}")
    
    # Salvar cache periodicamente (a cada 10 entradas)
    if len(GEOCODING_CACHE) % 10 == 0:
        save_geocoding_cache()

# Função para obter o caminho base (funciona tanto em desenvolvimento quanto como executável)
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Se estamos rodando como executável
        return sys._MEIPASS
    else:
        # Se estamos rodando como script Python
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """Obtém o caminho absoluto para um recurso, funciona tanto em desenvolvimento quanto como executável"""
    if getattr(sys, 'frozen', False):
        # Se estamos rodando como executável
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Se estamos rodando como script Python
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# Configuração do Flask
app = Flask(__name__, 
           static_folder=get_resource_path("static"), 
           template_folder=get_resource_path("templates"))

# Configurar CORS para permitir requisições do Django
from flask_cors import CORS
CORS(app, origins=['http://127.0.0.1:8000', 'http://localhost:8000'])

# Habilitar compressão e cache estático (silencioso se lib ausente)
try:
    from flask_compress import Compress
    app.config['COMPRESS_MIMETYPES'] = ['text/html','text/css','application/json','application/javascript']
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    Compress(app)
except Exception:
    pass
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800

# Configuração de logging para produção (silencioso)
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

# Pastas para os arquivos (estrutura organizada em Mapas/)
PASTA_KMLS = get_resource_path("Mapas/kml")
PASTA_KMZS = get_resource_path("Mapas/kmz")
PASTA_CSVS = get_resource_path("Mapas/csv")
PASTA_XLS = get_resource_path("Mapas/xls")
PASTA_XLSX = get_resource_path("Mapas/xlsx")

# Configuração de roteamento - OSRM (gratuito)
print("Sistema de roteamento OSRM configurado - roteamento por ruas ativado!")
HTTP_SESSION = requests.Session()

# ===== Cache de CTOs para acelerar verificações =====
CTOS_CACHE = []
CTOS_CACHE_BUILT_AT = 0
CTOS_CACHE_TTL = 300  # 5 minutos

class LRUTTLCache:
    """Cache LRU com TTL (Time To Live) para otimizar consultas"""
    def __init__(self, max_size=1000, ttl=600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key):
        now = time.time()
        entry = self.cache.get(key)
        if not entry:
            return None
        ts, value = entry
        if now - ts > self.ttl:
            try:
                del self.cache[key]
            except KeyError:
                pass
            return None
        self.cache.move_to_end(key)
        return value
    
    def set(self, key, value):
        now = time.time()
        self.cache[key] = (now, value)
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

# Inicializar caches
route_cache = LRUTTLCache(max_size=MAX_CACHE_SIZE, ttl=1800)
viability_cache = LRUTTLCache(max_size=1000, ttl=600)

def ler_kml(caminho_kml):
    """Lê um arquivo KML e extrai coordenadas"""
    try:
        tree = ET.parse(caminho_kml)
        root = tree.getroot()
        
        # Namespace do KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        coordenadas = []
        
        # Buscar por elementos Placemark
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
    try:
        with zipfile.ZipFile(caminho_kmz, 'r') as kmz:
            for arquivo in kmz.namelist():
                if arquivo.endswith('.kml'):
                    with kmz.open(arquivo) as kml_file:
                        # Salvar temporariamente o KML
                        temp_kml = 'temp.kml'
                        with open(temp_kml, 'wb') as f:
                            f.write(kml_file.read())
                        
                        coordenadas = ler_kml(temp_kml)
                        
                        # Remover arquivo temporário
                        if os.path.exists(temp_kml):
                            os.remove(temp_kml)
                        
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
        
        # Tentar detectar o delimitador automaticamente
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
        
        # Ler o CSV com pandas
        df = pd.read_csv(caminho_csv, delimiter=delimiter, encoding='utf-8')
        
        # Procurar por colunas de latitude e longitude
        lat_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'latitude', 'y'])]
        lng_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'longitude', 'x'])]
        nome_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['nome', 'name', 'id', 'cto'])]
        
        if not lat_cols or not lng_cols:
            # Se não encontrar colunas óbvias, tentar usar as primeiras duas colunas numéricas
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
        
        # Ler o arquivo Excel
        df = pd.read_excel(caminho_excel)
        
        # Procurar por colunas de latitude e longitude
        lat_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lat', 'latitude', 'y'])]
        lng_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'longitude', 'x'])]
        nome_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['nome', 'name', 'id', 'cto'])]
        
        if not lat_cols or not lng_cols:
            # Se não encontrar colunas óbvias, tentar usar as primeiras duas colunas numéricas
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
    """
    Calcula a distância entre dois pontos usando a fórmula de Haversine
    Retorna a distância em metros
    """
    # Raio da Terra em metros
    R = 6371000
    
    # Converter graus para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Distância em metros
    distancia = R * c
    return distancia

def calcular_rota_ruas_single(lat1, lon1, lat2, lon2, cto_info=None):
    """
    Versão single-threaded da função calcular_rota_ruas para uso em paralelo
    """
    try:
        cache_key = f"{lat1:.6f},{lon1:.6f}->{lat2:.6f},{lon2:.6f}"
        cached = route_cache.get(cache_key)
        if cached:
            return cached[0], cached[1], cto_info
        
        base_url = "https://router.project-osrm.org/route/v1/driving"
        url = f"{base_url}/{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
        params = {
            "overview": "simplified",
            "geometries": "geojson",
            "alternatives": "false",
            "steps": "false"
        }
        headers = {"User-Agent": "CastroX-FTTH-KML/1.0"}
        resp = HTTP_SESSION.get(url, params=params, headers=headers, timeout=ROUTING_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("routes"):
            route = data["routes"][0]
            distancia = float(route.get("distance", calcular_distancia(lat1, lon1, lat2, lon2)))
            coords = route.get("geometry", {}).get("coordinates") or [[lon1, lat1], [lon2, lat2]]
            route_cache.set(cache_key, (distancia, coords))
            return distancia, coords, cto_info
    except Exception as e:
        print(f"Erro ao calcular rota OSRM: {e}")
    
    # Fallback para distância euclidiana
    distancia = calcular_distancia(lat1, lon1, lat2, lon2)
    coords = [[lon1, lat1], [lon2, lat2]]
    try:
        route_cache.set(cache_key, (distancia, coords))
    except Exception:
        pass
    return distancia, coords, cto_info

def calcular_rota_ruas(lat1, lon1, lat2, lon2):
    """
    Calcula rota usando OSRM (driving) e retorna (distancia_metros, geometria)
    geometria é uma lista de [lon, lat]. Usa cache LRU+TTL.
    """
    try:
        cache_key = f"{lat1:.6f},{lon1:.6f}->{lat2:.6f},{lon2:.6f}"
        cached = route_cache.get(cache_key)
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
        headers = {"User-Agent": "CastroX-FTTH-KML/1.0"}
        resp = HTTP_SESSION.get(url, params=params, headers=headers, timeout=ROUTING_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("routes"):
            route = data["routes"][0]
            distancia = float(route.get("distance", calcular_distancia(lat1, lon1, lat2, lon2)))
            coords = route.get("geometry", {}).get("coordinates") or [[lon1, lat1], [lon2, lat2]]
            route_cache.set(cache_key, (distancia, coords))
            return distancia, coords
    except Exception as e:
        print(f"Erro ao calcular rota OSRM: {e}")
    distancia = calcular_distancia(lat1, lon1, lat2, lon2)
    coords = [[lon1, lat1], [lon2, lat2]]
    try:
        route_cache.set(cache_key, (distancia, coords))
    except Exception:
        pass
    return distancia, coords

def classificar_viabilidade(distancia_metros):
    """
    Classifica a viabilidade baseada na distância
    """
    if distancia_metros <= 300:
        return {
            "status": "Viável",
            "cor": "#28a745",  # Verde
            "descricao": "Instalação viável"
        }
    elif distancia_metros <= 1000:
        return {
            "status": "Viabilidade Limitada", 
            "cor": "#ffc107",  # Amarelo
            "descricao": "Instalação com limitações"
        }
    else:
        return {
            "status": "Sem viabilidade",
            "cor": "#dc3545",  # Vermelho
            "descricao": "Instalação não viável"
        }

def get_all_ctos(use_cache=True):
    """Retorna lista de todos os CTOs com nome do arquivo, usando cache em memória."""
    global CTOS_CACHE, CTOS_CACHE_BUILT_AT
    now = time.time()
    if use_cache and CTOS_CACHE and (now - CTOS_CACHE_BUILT_AT) < CTOS_CACHE_TTL:
        return CTOS_CACHE

    coords = []
    # KMLs
    if os.path.exists(PASTA_KMLS):
        arquivos_kml = [f for f in os.listdir(PASTA_KMLS) if f.lower().endswith(".kml")]
        for arquivo in arquivos_kml:
            caminho = os.path.join(PASTA_KMLS, arquivo)
            for coord in ler_kml(caminho):
                coord["arquivo"] = arquivo
                coords.append(coord)
    # KMZs
    if os.path.exists(PASTA_KMZS):
        arquivos_kmz = [f for f in os.listdir(PASTA_KMZS) if f.lower().endswith(".kmz")]
        for arquivo in arquivos_kmz:
            caminho = os.path.join(PASTA_KMZS, arquivo)
            for coord in ler_kmz(caminho):
                coord["arquivo"] = arquivo
                coords.append(coord)
    # CSVs
    if os.path.exists(PASTA_CSVS):
        arquivos_csv = [f for f in os.listdir(PASTA_CSVS) if f.lower().endswith(".csv")]
        for arquivo in arquivos_csv:
            caminho = os.path.join(PASTA_CSVS, arquivo)
            for coord in ler_csv(caminho):
                coord["arquivo"] = arquivo
                coords.append(coord)
    # XLS
    if os.path.exists(PASTA_XLS):
        arquivos_xls = [f for f in os.listdir(PASTA_XLS) if f.lower().endswith(".xls")]
        for arquivo in arquivos_xls:
            caminho = os.path.join(PASTA_XLS, arquivo)
            for coord in ler_excel(caminho):
                coord["arquivo"] = arquivo
                coords.append(coord)
    # XLSX
    if os.path.exists(PASTA_XLSX):
        arquivos_xlsx = [f for f in os.listdir(PASTA_XLSX) if f.lower().endswith(".xlsx")]
        for arquivo in arquivos_xlsx:
            caminho = os.path.join(PASTA_XLSX, arquivo)
            for coord in ler_excel(caminho):
                coord["arquivo"] = arquivo
                coords.append(coord)
    
    CTOS_CACHE = coords
    CTOS_CACHE_BUILT_AT = now
    return coords

# ===== ROTAS DA APLICAÇÃO =====

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    """Rota específica para favicon para evitar 404"""
    return '', 204

# Handler global para 404
@app.errorhandler(404)
def not_found_error(error):
    """Handler global para erros 404"""
    if request.path.startswith('/api/'):
        return jsonify({"erro": "Endpoint não encontrado"}), 404
    return '', 204

@app.route("/api/arquivos", methods=["GET"])
def listar_arquivos():
    """Lista todos os arquivos disponíveis (KML, KMZ, CSV, XLS, XLSX)"""
    arquivos = []
    
    # Listar arquivos KML
    if os.path.exists(PASTA_KMLS):
        for arquivo in os.listdir(PASTA_KMLS):
            if arquivo.endswith('.kml'):
                arquivos.append({
                    'nome': arquivo,
                    'tipo': 'kml',
                    'caminho': os.path.join(PASTA_KMLS, arquivo)
                })
    
    # Listar arquivos KMZ
    if os.path.exists(PASTA_KMZS):
        for arquivo in os.listdir(PASTA_KMZS):
            if arquivo.endswith('.kmz'):
                arquivos.append({
                    'nome': arquivo,
                    'tipo': 'kmz',
                    'caminho': os.path.join(PASTA_KMZS, arquivo)
                })
    
    # Listar arquivos CSV
    if os.path.exists(PASTA_CSVS):
        for arquivo in os.listdir(PASTA_CSVS):
            if arquivo.endswith('.csv'):
                arquivos.append({
                    'nome': arquivo,
                    'tipo': 'csv',
                    'caminho': os.path.join(PASTA_CSVS, arquivo)
                })
    
    # Listar arquivos XLS
    if os.path.exists(PASTA_XLS):
        for arquivo in os.listdir(PASTA_XLS):
            if arquivo.endswith('.xls'):
                arquivos.append({
                    'nome': arquivo,
                    'tipo': 'xls',
                    'caminho': os.path.join(PASTA_XLS, arquivo)
                })
    
    # Listar arquivos XLSX
    if os.path.exists(PASTA_XLSX):
        for arquivo in os.listdir(PASTA_XLSX):
            if arquivo.endswith('.xlsx'):
                arquivos.append({
                    'nome': arquivo,
                    'tipo': 'xlsx',
                    'caminho': os.path.join(PASTA_XLSX, arquivo)
                })
    
    return jsonify(arquivos)

@app.route("/api/coordenadas", methods=["GET"])
def coordenadas():
    """Retorna coordenadas de um arquivo específico"""
    arquivo = request.args.get('arquivo')
    if not arquivo:
        return jsonify({'erro': 'Arquivo não especificado'}), 400
    
    # Determinar o caminho completo e função de leitura
    if arquivo.endswith('.kml'):
        caminho = os.path.join(PASTA_KMLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kml(caminho)
        else:
            return jsonify({'erro': 'Arquivo KML não encontrado'}), 404
    elif arquivo.endswith('.kmz'):
        caminho = os.path.join(PASTA_KMZS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kmz(caminho)
        else:
            return jsonify({'erro': 'Arquivo KMZ não encontrado'}), 404
    elif arquivo.endswith('.csv'):
        caminho = os.path.join(PASTA_CSVS, arquivo)
        if os.path.exists(caminho):
            coords = ler_csv(caminho)
        else:
            return jsonify({'erro': 'Arquivo CSV não encontrado'}), 404
    elif arquivo.endswith('.xls'):
        caminho = os.path.join(PASTA_XLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo XLS não encontrado'}), 404
    elif arquivo.endswith('.xlsx'):
        caminho = os.path.join(PASTA_XLSX, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo XLSX não encontrado'}), 404
    else:
        return jsonify({'erro': 'Tipo de arquivo não suportado'}), 400
    
    return jsonify(coords)

@app.route("/api/contar-pontos", methods=["GET"])
def contar_pontos():
    """Conta o número de pontos em um arquivo"""
    arquivo = request.args.get('arquivo')
    if not arquivo:
        return jsonify({'erro': 'Arquivo não especificado'}), 400
    
    # Obter coordenadas baseado no tipo de arquivo
    if arquivo.endswith('.kml'):
        caminho = os.path.join(PASTA_KMLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kml(caminho)
        else:
            return jsonify({'erro': 'Arquivo não encontrado'}), 404
    elif arquivo.endswith('.kmz'):
        caminho = os.path.join(PASTA_KMZS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kmz(caminho)
        else:
            return jsonify({'erro': 'Arquivo não encontrado'}), 404
    elif arquivo.endswith('.csv'):
        caminho = os.path.join(PASTA_CSVS, arquivo)
        if os.path.exists(caminho):
            coords = ler_csv(caminho)
        else:
            return jsonify({'erro': 'Arquivo não encontrado'}), 404
    elif arquivo.endswith('.xls'):
        caminho = os.path.join(PASTA_XLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo não encontrado'}), 404
    elif arquivo.endswith('.xlsx'):
        caminho = os.path.join(PASTA_XLSX, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo não encontrado'}), 404
    else:
        return jsonify({'erro': 'Tipo de arquivo não suportado'}), 400
    
    # Contar pontos
    total_pontos = 0
    for item in coords:
        if item.get('tipo') == 'point':
            total_pontos += 1
        elif item.get('tipo') == 'line':
            total_pontos += len(item.get('coordenadas', []))
    
    return jsonify({'total': total_pontos})

@app.route("/api/coordenadas-filtradas", methods=["GET"])
def coordenadas_filtradas():
    """Retorna coordenadas filtradas para o Brasil"""
    arquivo = request.args.get('arquivo')
    if not arquivo:
        return jsonify({'erro': 'Arquivo não especificado'}), 400
    
    # Determinar o caminho completo e função de leitura
    if arquivo.endswith('.kml'):
        caminho = os.path.join(PASTA_KMLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kml(caminho)
        else:
            return jsonify({'erro': 'Arquivo KML não encontrado'}), 404
    elif arquivo.endswith('.kmz'):
        caminho = os.path.join(PASTA_KMZS, arquivo)
        if os.path.exists(caminho):
            coords = ler_kmz(caminho, filtrar_brasil=True)
        else:
            return jsonify({'erro': 'Arquivo KMZ não encontrado'}), 404
    elif arquivo.endswith('.csv'):
        caminho = os.path.join(PASTA_CSVS, arquivo)
        if os.path.exists(caminho):
            coords = ler_csv(caminho)
        else:
            return jsonify({'erro': 'Arquivo CSV não encontrado'}), 404
    elif arquivo.endswith('.xls'):
        caminho = os.path.join(PASTA_XLS, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo XLS não encontrado'}), 404
    elif arquivo.endswith('.xlsx'):
        caminho = os.path.join(PASTA_XLSX, arquivo)
        if os.path.exists(caminho):
            coords = ler_excel(caminho)
        else:
            return jsonify({'erro': 'Arquivo XLSX não encontrado'}), 404
    else:
        return jsonify({'erro': 'Tipo de arquivo não suportado'}), 400
    
    # Aplicar filtro do Brasil para todos os tipos exceto KMZ (que já vem filtrado)
    if not arquivo.endswith('.kmz'):
        coords = filtrar_coordenadas_brasil(coords)
    
    return jsonify(coords)

@app.route("/api/geocode", methods=["GET"])
def geocode():
    """Geocodificação usando OpenStreetMap Nominatim com cache"""
    endereco = request.args.get('endereco')
    if not endereco:
        return jsonify({'erro': 'Endereço não especificado'}), 400
    
    # Verificar cache primeiro
    cached_result = get_cached_geocoding(endereco)
    if cached_result:
        return jsonify(cached_result)
    
    try:
        print(f"Geocodificando: {endereco}")
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': endereco,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'br'  # Limitar ao Brasil
        }
        headers = {'User-Agent': 'FTTH-KML-Viewer/1.0'}
        
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
            return jsonify(geocoding_result)
        else:
            return jsonify({'erro': 'Endereço não encontrado'}), 404
            
    except Exception as e:
        return jsonify({'erro': f'Erro na geocodificação: {str(e)}'}), 500

@app.route("/api/cache/geocoding/stats", methods=["GET"])
def geocoding_cache_stats():
    """Retorna estatísticas do cache de geocodificação"""
    try:
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for endereco, cache_entry in GEOCODING_CACHE.items():
            if current_time - cache_entry['timestamp'] < GEOCODING_CACHE_TTL:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return jsonify({
            'total_entries': len(GEOCODING_CACHE),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl_hours': GEOCODING_CACHE_TTL / 3600,
            'max_size': GEOCODING_CACHE_MAX_SIZE
        })
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter estatísticas: {str(e)}'}), 500

@app.route("/api/cache/geocoding/clear", methods=["POST"])
def clear_geocoding_cache():
    """Limpa o cache de geocodificação"""
    try:
        global GEOCODING_CACHE
        GEOCODING_CACHE.clear()
        save_geocoding_cache()
        return jsonify({'mensagem': 'Cache de geocodificação limpo com sucesso'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao limpar cache: {str(e)}'}), 500

@app.route("/api/verificar", methods=["POST"])
def verificar_arquivo_django():
    """Endpoint específico para integração com Django"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['file_path', 'file_type', 'company_id', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}'
                }), 400
        
        file_path = data['file_path']
        file_type = data['file_type']
        company_id = data['company_id']
        user_id = data['user_id']
        options = data.get('options', {})
        
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}'
            }), 404
        
        # Gerar ID único para a análise
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # Processar arquivo baseado no tipo
        start_time = time.time()
        
        if file_type.lower() in ['xlsx', 'xls']:
            coords = ler_excel(file_path)
        elif file_type.lower() == 'csv':
            coords = ler_csv(file_path)
        elif file_type.lower() in ['kml', 'kmz']:
            if file_type.lower() == 'kmz':
                coords = ler_kmz(file_path)
            else:
                coords = ler_kml(file_path)
        else:
            return jsonify({
                'success': False,
                'error': f'Tipo de arquivo não suportado: {file_type}'
            }), 400
        
        processing_time = time.time() - start_time
        
        # Calcular score de viabilidade (simulado)
        viability_score = min(100, max(0, 100 - len(coords) * 0.1))
        
        # Gerar issues e recomendações baseadas no arquivo
        issues = []
        recommendations = []
        
        if len(coords) == 0:
            issues.append("Nenhuma coordenada encontrada no arquivo")
            recommendations.append("Verifique o formato do arquivo")
        elif len(coords) > 1000:
            issues.append("Muitas coordenadas podem impactar a performance")
            recommendations.append("Considere dividir o arquivo em partes menores")
        
        # Preparar resposta
        result = {
            'success': True,
            'analysis_id': analysis_id,
            'status': 'completed',
            'results': {
                'viability_score': int(viability_score),
                'issues': issues,
                'recommendations': recommendations,
                'coordinates_count': len(coords),
                'processing_time': round(processing_time, 2),
                'file_info': {
                    'name': os.path.basename(file_path),
                    'type': file_type,
                    'size': os.path.getsize(file_path)
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro na verificação Django: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/verificar-viabilidade", methods=["GET"])
def verificar_viabilidade():
    """Verifica viabilidade de instalação FTTH - Versão Otimizada"""
    try:
        # Para requisições GET, usar request.args
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        
        if lat is None or lon is None:
            return jsonify({"erro": "Coordenadas não fornecidas"}), 400
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return jsonify({"erro": "Coordenadas inválidas"}), 400
        
        # Verificar cache
        cache_key = f"{lat:.6f},{lon:.6f}"
        cached_result = viability_cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)
        
        # Buscar CTOs
        ctos = get_all_ctos()
        if not ctos:
            return jsonify({"erro": "Nenhum CTO encontrado"}), 404
        
        # ABORDAGEM HÍBRIDA OTIMIZADA:
        # 1. Filtro rápido por distância euclidiana
        # 2. Cálculo de rota real apenas para os melhores candidatos
        
        print(f"Fase 1: Filtrando {len(ctos)} CTOs por distância euclidiana...")
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
            return jsonify({"erro": "Nenhum CTO válido encontrado"}), 404
        
        # Ordenar por distância euclidiana e pegar os 5 melhores candidatos (otimizado)
        ctos_com_distancia.sort(key=lambda x: x["distancia_euclidiana"])
        num_candidatos = min(5, len(ctos_com_distancia))
        ctos_candidatos = ctos_com_distancia[:num_candidatos]
        
        print(f"Fase 2: Calculando rota real para os {num_candidatos} melhores candidatos (PARALELO)...")
        
        # Processamento paralelo dos cálculos OSRM
        cto_mais_proximo = None
        menor_distancia = float('inf')
        melhor_geometria = None
        
        # Preparar tarefas para processamento paralelo
        tarefas = []
        for i, cto in enumerate(ctos_candidatos):
            try:
                cto_lat = float(cto["lat"])
                cto_lon = float(cto["lng"])
                tarefas.append((lat, lon, cto_lat, cto_lon, cto))
            except (ValueError, TypeError, KeyError):
                continue
        
        # Executar cálculos em paralelo (máximo 4 threads para não sobrecarregar OSRM)
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submeter todas as tarefas
            futures = {
                executor.submit(calcular_rota_ruas_single, tarefa[0], tarefa[1], tarefa[2], tarefa[3], tarefa[4]): i 
                for i, tarefa in enumerate(tarefas)
            }
            
            # Processar resultados conforme completam
            for future in as_completed(futures):
                try:
                    distancia_ruas, geometria, cto = future.result()
                    i = futures[future]
                    print(f"Rota {i+1}/{len(tarefas)} - {cto.get('nome', 'CTO')} (euclidiana: {cto['distancia_euclidiana']:.0f}m)")
                    print(f"   Rota real: {distancia_ruas:.2f}m")
                    
                    if distancia_ruas < menor_distancia:
                        menor_distancia = distancia_ruas
                        cto_mais_proximo = cto
                        melhor_geometria = geometria
                        print(f"   Novo melhor CTO!")
                        
                except Exception as e:
                    print(f"   Erro no processamento paralelo: {e}")
                    continue
        
        if not cto_mais_proximo:
            return jsonify({"erro": "Nenhum CTO válido encontrado"}), 404
        
        # Usar a melhor geometria já calculada
        distancia_ruas = menor_distancia
        geometria = melhor_geometria
        
        # Log de debug
        cto_lat = float(cto_mais_proximo["lat"])
        cto_lon = float(cto_mais_proximo["lng"])
        print(f"[DEBUG] CTO mais próximo selecionado: {cto_mais_proximo.get('nome', 'CTO')} ({cto_mais_proximo.get('arquivo', '')})")
        print(f"[DEBUG] Coordenadas do CTO: {cto_lat}, {cto_lon}")
        print(f"[DEBUG] Distância pelas ruas: {distancia_ruas:.2f} metros")
        
        # Classificar viabilidade
        viabilidade = classificar_viabilidade(distancia_ruas)
        
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
                "metros": round(distancia_ruas, 2),
                "km": round(distancia_ruas / 1000, 3)
            },
            "rota": {
                "geometria": geometria
            }
        }
        
        # Salvar no cache
        viability_cache.set(cache_key, resultado)
        
        return jsonify(resultado)
        
    except Exception as e:
        import traceback
        print(f"Erro na verificação de viabilidade: {e}")
        print(f"Traceback completo: {traceback.format_exc()}")
        return jsonify({"erro": f"Erro interno do servidor: {str(e)}"}), 500


def _start_server_in_background():
    """Inicia o servidor Flask em background"""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Inicializar cache de geocodificação
    load_geocoding_cache()
    
    # Criar pastas se não existirem
    if not os.path.exists(PASTA_KMLS):
        os.makedirs(PASTA_KMLS)
    if not os.path.exists(PASTA_KMZS):
        os.makedirs(PASTA_KMZS)
    if not os.path.exists(PASTA_CSVS):
        os.makedirs(PASTA_CSVS)
    if not os.path.exists(PASTA_XLS):
        os.makedirs(PASTA_XLS)
    if not os.path.exists(PASTA_XLSX):
        os.makedirs(PASTA_XLSX)
    
    # Verificar se deve rodar em modo desktop ou servidor
    if len(sys.argv) > 1 and sys.argv[1] == '--desktop':
        print("Verificador CastroX iniciado em modo desktop!")
        _start_server_in_background()
        try:
            import webview
            # Aguardar servidor iniciar
            for _ in range(30):
                try:
                    HTTP_SESSION.get('http://127.0.0.1:5000', timeout=0.5)
                    break
                except Exception:
                    time.sleep(0.2)
            webview.create_window('FTTH KML Viewer', 'http://127.0.0.1:5000/', width=1100, height=800, resizable=True)
            webview.start(gui='edgechromium')
        except Exception as e:
            print(f"WebView indisponível ({e}). Abrindo navegador padrão...")
            webbrowser.open('http://127.0.0.1:5000')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nServidor encerrado.")
    else:
        # Modo servidor normal
        print("\n=== ROTAS REGISTRADAS ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule} -> {rule.endpoint} (methods: {list(rule.methods)})")
        print("========================\n")
        
        print("Iniciando FTTH KML Viewer...")
        print("Acesse: http://127.0.0.1:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)

