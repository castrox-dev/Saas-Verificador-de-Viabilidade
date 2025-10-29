"""
Funções auxiliares para processamento de arquivos KML/KMZ/CSV/XLS e cálculos geográficos
Migrado do Verificador-De-Viabilidade-main
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


def get_all_ctos():
    """Retorna todos os CTOs de todos os arquivos com cache"""
    from .file_readers import FileReaderService
    
    # Verificar cache primeiro
    cache_key = "all_ctos_global"
    cached_ctos = cache.get(cache_key)
    if cached_ctos:
        return cached_ctos
    
    coords = []
    
    # KMLs
    kml_dir = getattr(settings, 'FTTH_KML_DIR', None)
    if kml_dir and os.path.exists(kml_dir):
        for arquivo in os.listdir(kml_dir):
            if arquivo.lower().endswith('.kml'):
                caminho = os.path.join(kml_dir, arquivo)
                try:
                    for coord in FileReaderService.ler_kml(caminho):
                        coord["arquivo"] = arquivo
                        coords.append(coord)
                except Exception as e:
                    print(f"Erro ao ler KML {arquivo}: {e}")
                    continue
    
    # KMZs
    kmz_dir = getattr(settings, 'FTTH_KMZ_DIR', None)
    if kmz_dir and os.path.exists(kmz_dir):
        for arquivo in os.listdir(kmz_dir):
            if arquivo.lower().endswith('.kmz'):
                caminho = os.path.join(kmz_dir, arquivo)
                try:
                    for coord in FileReaderService.ler_kmz(caminho):
                        coord["arquivo"] = arquivo
                        coords.append(coord)
                except Exception as e:
                    print(f"Erro ao ler KMZ {arquivo}: {e}")
                    continue
    
    # CSVs
    csv_dir = getattr(settings, 'FTTH_CSV_DIR', None)
    if csv_dir and os.path.exists(csv_dir):
        for arquivo in os.listdir(csv_dir):
            if arquivo.lower().endswith('.csv'):
                caminho = os.path.join(csv_dir, arquivo)
                try:
                    for coord in FileReaderService.ler_csv(caminho):
                        coord["arquivo"] = arquivo
                        coords.append(coord)
                except Exception as e:
                    print(f"Erro ao ler CSV {arquivo}: {e}")
                    continue
    
    # XLS
    xls_dir = getattr(settings, 'FTTH_XLS_DIR', None)
    if xls_dir and os.path.exists(xls_dir):
        for arquivo in os.listdir(xls_dir):
            if arquivo.lower().endswith('.xls'):
                caminho = os.path.join(xls_dir, arquivo)
                try:
                    for coord in FileReaderService.ler_excel(caminho):
                        coord["arquivo"] = arquivo
                        coords.append(coord)
                except Exception as e:
                    print(f"Erro ao ler XLS {arquivo}: {e}")
                    continue
    
    # XLSX
    xlsx_dir = getattr(settings, 'FTTH_XLSX_DIR', None)
    if xlsx_dir and os.path.exists(xlsx_dir):
        for arquivo in os.listdir(xlsx_dir):
            if arquivo.lower().endswith('.xlsx'):
                caminho = os.path.join(xlsx_dir, arquivo)
                try:
                    for coord in FileReaderService.ler_excel(caminho):
                        coord["arquivo"] = arquivo
                        coords.append(coord)
                except Exception as e:
                    print(f"Erro ao ler XLSX {arquivo}: {e}")
                    continue
    
    # Salvar no cache por 1 hora
    cache.set(cache_key, coords, 3600)
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


def calcular_rota_ruas_single(lat1, lon1, lat2, lon2, cto_info=None):
    """Versão single-threaded para processamento paralelo"""
    from .routing import RoutingService
    distancia, coords = RoutingService.calcular_rota_ruas(lat1, lon1, lat2, lon2)
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
