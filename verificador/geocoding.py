"""
Serviço de geocodificação usando OpenStreetMap Nominatim
Migrado do Flask ftth_kml_app.py
"""
import requests
import logging
import time
from typing import Optional, Dict
from django.core.cache import cache
from django.conf import settings
from .utils import get_cached_geocoding, set_cached_geocoding

logger = logging.getLogger(__name__)


class GeocodingService:
    """Serviço para geocodificação de endereços"""
    
    # Configurações
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    CACHE_TTL = 86400  # 24 horas
    TIMEOUT = 10
    
    @classmethod
    def geocodificar(cls, endereco: str) -> Optional[Dict]:
        """
        Geocodifica um endereço usando OpenStreetMap Nominatim com cache
        
        Args:
            endereco: Endereço para geocodificar
            
        Returns:
            Dict com lat, lng e endereco_completo, ou None se não encontrado
        """
        if not endereco:
            return None
        
        # Verificar cache persistente primeiro
        cached_result = get_cached_geocoding(endereco)
        if cached_result:
            logger.debug(f"Cache HIT para geocodificação: {endereco}")
            return cached_result
        
        try:
            logger.info(f"Geocodificando: {endereco}")
            params = {
                'q': endereco,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'br'  # Limitar ao Brasil
            }
            headers = {'User-Agent': 'Django-FTTH-Verificador/1.0'}
            
            response = requests.get(cls.BASE_URL, params=params, headers=headers, timeout=cls.TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data:
                resultado = data[0]
                geocoding_result = {
                    'lat': float(resultado['lat']),
                    'lng': float(resultado['lon']),
                    'endereco_completo': resultado['display_name']
                }
                
                # Armazenar no cache persistente
                set_cached_geocoding(endereco, geocoding_result)
                logger.info(f"Geocodificação bem-sucedida: {endereco}")
                return geocoding_result
            else:
                logger.warning(f"Endereço não encontrado: {endereco}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na geocodificação de {endereco}: {e}")
            return None
    
    @classmethod
    def obter_estatisticas_cache(cls) -> Dict:
        """Retorna estatísticas do cache de geocodificação"""
        # Como estamos usando Django cache, não temos acesso direto às estatísticas
        # Mas podemos retornar informações básicas
        return {
            'backend': cache.__class__.__name__,
            'cache_ttl_hours': cls.CACHE_TTL / 3600,
        }
    
    @classmethod
    def limpar_cache(cls):
        """Limpa o cache de geocodificação"""
        # Django cache não tem método para limpar apenas prefixos específicos
        # Isso limparia todo o cache - use com cuidado
        try:
            cache.clear()
            return {'mensagem': 'Cache limpo com sucesso'}
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return {'erro': str(e)}
