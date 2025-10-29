"""
Serviço de roteamento usando OSRM e cálculo de distâncias
Migrado do Flask ftth_kml_app.py
"""
import math
import requests
import logging
from collections import OrderedDict
from typing import Tuple, List, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class RoutingService:
    """Serviço para cálculo de rotas e distâncias"""
    
    # Configurações
    ROUTING_TIMEOUT = getattr(settings, 'ROUTING_TIMEOUT', 15)
    BASE_URL = "https://router.project-osrm.org/route/v1/driving"
    OPENROUTESERVICE_API_KEY = getattr(settings, 'OPENROUTESERVICE_API_KEY', '')
    
    # Session HTTP compartilhada
    _session = None
    
    @classmethod
    def get_session(cls):
        """Retorna sessão HTTP compartilhada"""
        if cls._session is None:
            cls._session = requests.Session()
        return cls._session
    
    @staticmethod
    def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    @classmethod
    def calcular_rota_ruas(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, List]:
        """
        Calcula rota usando OSRM (driving) e retorna (distancia_metros, geometria)
        geometria é uma lista de [lon, lat]. Usa cache do Django.
        """
        # Chave de cache
        cache_key = f"route_{lat1:.6f},{lon1:.6f}->{lat2:.6f},{lon2:.6f}"
        
        # Tentar obter do cache
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{cls.BASE_URL}/{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
            params = {
                "overview": "simplified",
                "geometries": "geojson",
                "alternatives": "false",
                "steps": "false"
            }
            headers = {"User-Agent": "Django-FTTH-Verificador/1.0"}
            
            session = cls.get_session()
            resp = session.get(url, params=params, headers=headers, timeout=cls.ROUTING_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("routes"):
                route = data["routes"][0]
                distancia = float(route.get("distance", cls.calcular_distancia(lat1, lon1, lat2, lon2)))
                coords = route.get("geometry", {}).get("coordinates") or [[lon1, lat1], [lon2, lat2]]
                result = (distancia, coords)
                
                # Salvar no cache (30 minutos)
                cache.set(cache_key, result, 1800)
                return result
        except Exception as e:
            logger.warning(f"Erro ao calcular rota OSRM: {e}")
        
        # Fallback para distância euclidiana
        distancia = cls.calcular_distancia(lat1, lon1, lat2, lon2)
        coords = [[lon1, lat1], [lon2, lat2]]
        result = (distancia, coords)
        
        # Salvar no cache mesmo para fallback
        cache.set(cache_key, result, 1800)
        return result
    
    @staticmethod
    def classificar_viabilidade(distancia_metros: float) -> dict:
        """
        Classifica a viabilidade baseada na distância usando configurações do settings
        """
        config = getattr(settings, 'FTTH_VIABILIDADE_CONFIG', {
            'viavel': 300,
            'limitada': 800,
            'inviavel': 800
        })
        
        if distancia_metros <= config['viavel']:
            return {
                "status": "Viável",
                "cor": "#28a745",  # Verde
                "descricao": "Instalação viável"
            }
        elif distancia_metros <= config['limitada']:
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
