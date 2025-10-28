"""
Serviços para leitura de arquivos de mapas (KML, KMZ, CSV, Excel)
Migrado do Flask ftth_kml_app.py
"""
import os
import csv
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FileReaderService:
    """Serviço para leitura de diferentes formatos de arquivos de mapas"""
    
    @staticmethod
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
            logger.error(f"Erro ao ler KML {caminho_kml}: {e}")
            return []
    
    @staticmethod
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
                            
                            coordenadas = FileReaderService.ler_kml(temp_kml)
                            
                            # Remover arquivo temporário
                            if os.path.exists(temp_kml):
                                os.remove(temp_kml)
                            
                            if filtrar_brasil:
                                coordenadas = FileReaderService.filtrar_coordenadas_brasil(coordenadas)
                            
                            return coordenadas
            return []
        except Exception as e:
            logger.error(f"Erro ao ler KMZ {caminho_kmz}: {e}")
            return []
    
    @staticmethod
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
    
    @staticmethod
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
            logger.error(f"Erro ao ler CSV {caminho_csv}: {e}")
            return []
    
    @staticmethod
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
            logger.error(f"Erro ao ler Excel {caminho_excel}: {e}")
            return []
    
    @staticmethod
    def ler_arquivo(caminho_arquivo):
        """Lê um arquivo automaticamente baseado na extensão"""
        if not os.path.exists(caminho_arquivo):
            return []
        
        ext = os.path.splitext(caminho_arquivo)[1].lower()
        
        if ext == '.kml':
            return FileReaderService.ler_kml(caminho_arquivo)
        elif ext == '.kmz':
            return FileReaderService.ler_kmz(caminho_arquivo)
        elif ext == '.csv':
            return FileReaderService.ler_csv(caminho_arquivo)
        elif ext in ['.xls', '.xlsx']:
            return FileReaderService.ler_excel(caminho_arquivo)
        else:
            logger.warning(f"Tipo de arquivo não suportado: {ext}")
            return []
