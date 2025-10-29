"""
Serviço principal de verificação de viabilidade
Migrado do Flask ftth_kml_app.py
"""
import os
import time
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.cache import cache
from django.conf import settings

from .file_readers import FileReaderService
from .routing import RoutingService
from .utils import get_all_ctos, classificar_viabilidade
from core.models import CTOMapFile, Company

logger = logging.getLogger(__name__)


class VerificadorService:
    """Serviço principal para verificação de viabilidade"""
    
    CACHE_TTL = 300  # 5 minutos
    
    @classmethod
    def verificar_arquivo(cls, arquivo_path: str, file_type: str) -> Dict:
        """
        Verifica viabilidade de um arquivo CTO
        
        Args:
            arquivo_path: Caminho do arquivo
            file_type: Tipo do arquivo (kml, kmz, csv, xls, xlsx)
            
        Returns:
            Dict com resultados da análise
        """
        try:
            start_time = time.time()
            
            # Ler coordenadas do arquivo
            coords = FileReaderService.ler_arquivo(arquivo_path)
            
            processing_time = time.time() - start_time
            
            # Calcular score de viabilidade (simulado - pode ser melhorado)
            viability_score = min(100, max(0, 100 - len(coords) * 0.1))
            
            # Gerar issues e recomendações
            issues = []
            recommendations = []
            
            if len(coords) == 0:
                issues.append("Nenhuma coordenada encontrada no arquivo")
                recommendations.append("Verifique o formato do arquivo")
            elif len(coords) > 1000:
                issues.append("Muitas coordenadas podem impactar a performance")
                recommendations.append("Considere dividir o arquivo em partes menores")
            
            return {
                'success': True,
                'results': {
                    'viability_score': int(viability_score),
                    'issues': issues,
                    'recommendations': recommendations,
                    'coordinates_count': len(coords),
                    'processing_time': round(processing_time, 2),
                    'file_info': {
                        'name': os.path.basename(arquivo_path),
                        'type': file_type,
                        'size': os.path.getsize(arquivo_path) if os.path.exists(arquivo_path) else 0
                    }
                }
            }
        except Exception as e:
            logger.error(f"Erro ao verificar arquivo {arquivo_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def verificar_viabilidade_coordenada(cls, lat: float, lon: float, company: Company) -> Dict:
        """
        Verifica viabilidade de instalação FTTH para uma coordenada específica
        
        Args:
            lat: Latitude
            lon: Longitude
            company: Empresa do usuário
            
        Returns:
            Dict com resultados da verificação
        """
        try:
            # Verificar cache
            cache_key = f"viability_{lat:.6f},{lon:.6f}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Buscar CTOs da empresa
            ctos = cls._obter_ctos_empresa(company)
            
            if not ctos:
                return {
                    "erro": "Nenhum CTO encontrado para esta empresa"
                }
            
            # Abordagem híbrida otimizada:
            # 1. Filtro rápido por distância euclidiana
            # 2. Cálculo de rota real apenas para os melhores candidatos
            
            logger.debug(f"Filtrando {len(ctos)} CTOs por distância euclidiana...")
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
                return {"erro": "Nenhum CTO válido encontrado"}
            
            # Ordenar por distância euclidiana e pegar os 5 melhores candidatos
            ctos_com_distancia.sort(key=lambda x: x["distancia_euclidiana"])
            num_candidatos = min(5, len(ctos_com_distancia))
            ctos_candidatos = ctos_com_distancia[:num_candidatos]
            
            logger.debug(f"Calculando rota real para os {num_candidatos} melhores candidatos...")
            
            # Processamento paralelo dos cálculos OSRM
            cto_mais_proximo = None
            menor_distancia = float('inf')
            melhor_geometria = None
            
            # Preparar tarefas para processamento paralelo
            tarefas = []
            for cto in ctos_candidatos:
                try:
                    cto_lat = float(cto["lat"])
                    cto_lon = float(cto["lng"])
                    tarefas.append((lat, lon, cto_lat, cto_lon, cto))
                except (ValueError, TypeError, KeyError):
                    continue
            
            # Executar cálculos em paralelo (máximo 4 threads)
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(cls._calcular_rota_com_cto, tarefa[0], tarefa[1], tarefa[2], tarefa[3], tarefa[4]): i 
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
                        logger.warning(f"Erro no processamento paralelo: {e}")
                        continue
            
            if not cto_mais_proximo:
                return {"erro": "Nenhum CTO válido encontrado"}
            
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
            cache.set(cache_key, resultado, cls.CACHE_TTL)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na verificação de viabilidade: {e}")
            return {"erro": f"Erro interno: {str(e)}"}
    
    @classmethod
    def _obter_ctos_empresa(cls, company: Company) -> List[Dict]:
        """
        Obtém todos os CTOs de uma empresa dos mapas salvos
        Integra com sistema de diretórios FTTH e mapas da empresa
        """
        try:
            # Verificar cache primeiro
            cache_key = f"ctos_empresa_{company.slug}"
            cached_ctos = cache.get(cache_key)
            if cached_ctos:
                logger.debug(f"Cache HIT para CTOs da empresa {company.slug}")
                return cached_ctos
            
            ctos = []
            
            # 1. Buscar mapas CTO da empresa (sistema SaaS)
            mapas = CTOMapFile.objects.filter(
                company=company,
                is_processed=True
            ).select_related('company')
            
            for mapa in mapas:
                if not mapa.file:
                    continue
                
                arquivo_path = mapa.file.path if hasattr(mapa.file, 'path') else None
                if not arquivo_path or not os.path.exists(arquivo_path):
                    continue
                
                # Ler coordenadas do arquivo
                coords = FileReaderService.ler_arquivo(arquivo_path)
                
                # Adicionar informações do arquivo
                for coord in coords:
                    coord["arquivo"] = os.path.basename(arquivo_path)
                    coord["mapa_id"] = mapa.id
                    coord["fonte"] = "empresa"
                    ctos.append(coord)
            
            # 2. Buscar CTOs dos diretórios FTTH (sistema global)
            try:
                ctos_globais = get_all_ctos()
                for coord in ctos_globais:
                    coord["fonte"] = "global"
                    ctos.append(coord)
            except Exception as e:
                logger.warning(f"Erro ao carregar CTOs globais: {e}")
            
            # Salvar no cache por 30 minutos
            cache.set(cache_key, ctos, 1800)
            
            logger.info(f"CTOs encontrados para {company.name}: {len(ctos)} (Empresa: {len([c for c in ctos if c.get('fonte') == 'empresa'])}, Global: {len([c for c in ctos if c.get('fonte') == 'global'])})")
            return ctos
        except Exception as e:
            logger.error(f"Erro ao obter CTOs da empresa {company.slug}: {e}")
            return []
    
    @staticmethod
    def _calcular_rota_com_cto(lat1: float, lon1: float, lat2: float, lon2: float, cto: Dict):
        """
        Versão helper para cálculo de rota com informações do CTO
        """
        try:
            distancia_ruas, geometria = RoutingService.calcular_rota_ruas(lat1, lon1, lat2, lon2)
            return distancia_ruas, geometria, cto
        except Exception as e:
            logger.warning(f"Erro ao calcular rota: {e}")
            # Fallback para distância euclidiana
            distancia = RoutingService.calcular_distancia(lat1, lon1, lat2, lon2)
            geometria = [[lon1, lat1], [lon2, lat2]]
            return distancia, geometria, cto
