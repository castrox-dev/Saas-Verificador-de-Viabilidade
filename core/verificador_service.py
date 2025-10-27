"""
Serviço de integração com o verificador Flask
Comunica com o aplicativo Flask para análise de viabilidade
"""
import requests
import json
import os
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from core.models import CTOMapFile, Company, CustomUser
from core.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class VerificadorFlaskService:
    """Serviço para comunicação com o verificador Flask"""
    
    # URL base do verificador Flask
    FLASK_BASE_URL = getattr(settings, 'VERIFICADOR_FLASK_URL', 'http://127.0.0.1:5000')
    
    # Timeout para requisições
    TIMEOUT = getattr(settings, 'VERIFICADOR_TIMEOUT', 30)
    
    @classmethod
    def verificar_arquivo(cls, uploaded_file: UploadedFile, company: Company, user: CustomUser) -> Dict[str, Any]:
        """
        Verifica viabilidade de um arquivo CTO usando o Flask
        
        Args:
            uploaded_file: Arquivo enviado pelo usuário
            company: Empresa do usuário
            user: Usuário que fez o upload
            
        Returns:
            Dict com resultados da análise
        """
        try:
            # Salvar arquivo temporariamente
            temp_path = cls._save_temp_file(uploaded_file)
            
            # Preparar dados para o Flask
            data = {
                'file_path': temp_path,
                'file_type': cls._get_file_extension(uploaded_file.name),
                'company_id': company.id,
                'user_id': user.id,
                'options': {
                    'detailed_analysis': True,
                    'generate_report': True
                }
            }
            
            # Fazer requisição para o Flask
            response = cls._make_request('/api/verificar', data)
            
            # Limpar arquivo temporário
            cls._cleanup_temp_file(temp_path)
            
            # Log da ação
            AuditLogger.log_user_action(
                user=user,
                action='map_analysis',
                details={
                    'file_name': uploaded_file.name,
                    'file_size': uploaded_file.size,
                    'company': company.name,
                    'success': response.get('success', False)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na verificação Flask: {str(e)}")
            return {
                'success': False,
                'error': f'Erro na análise: {str(e)}',
                'status': 'failed'
            }
    
    @classmethod
    def verificar_coordenadas(cls, lat: float, lon: float, company: Company, user: CustomUser) -> Dict[str, Any]:
        """
        Verifica viabilidade de coordenadas específicas
        
        Args:
            lat: Latitude
            lon: Longitude
            company: Empresa do usuário
            user: Usuário que fez a verificação
            
        Returns:
            Dict com resultados da análise
        """
        try:
            # Fazer requisição para o Flask
            params = {
                'lat': lat,
                'lon': lon
            }
            
            response = cls._make_request('/api/verificar-viabilidade', params, method='GET')
            
            # Log da ação
            AuditLogger.log_user_action(
                user=user,
                action='coordinate_analysis',
                details={
                    'coordinates': f'{lat},{lon}',
                    'company': company.name,
                    'success': response.get('success', False)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na verificação de coordenadas: {str(e)}")
            return {
                'success': False,
                'error': f'Erro na análise: {str(e)}',
                'status': 'failed'
            }
    
    @classmethod
    def listar_arquivos_disponiveis(cls) -> List[Dict[str, Any]]:
        """
        Lista arquivos disponíveis no verificador Flask
        
        Returns:
            Lista de arquivos disponíveis
        """
        try:
            response = cls._make_request('/api/arquivos', method='GET')
            return response if isinstance(response, list) else []
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos Flask: {str(e)}")
            return []
    
    @classmethod
    def obter_coordenadas_arquivo(cls, arquivo: str) -> List[Dict[str, Any]]:
        """
        Obtém coordenadas de um arquivo específico
        
        Args:
            arquivo: Nome do arquivo
            
        Returns:
            Lista de coordenadas
        """
        try:
            params = {'arquivo': arquivo}
            response = cls._make_request('/api/coordenadas', params, method='GET')
            return response if isinstance(response, list) else []
            
        except Exception as e:
            logger.error(f"Erro ao obter coordenadas: {str(e)}")
            return []
    
    @classmethod
    def geocodificar_endereco(cls, endereco: str) -> Dict[str, Any]:
        """
        Geocodifica um endereço usando o Flask
        
        Args:
            endereco: Endereço para geocodificar
            
        Returns:
            Coordenadas do endereço
        """
        try:
            params = {'endereco': endereco}
            response = cls._make_request('/api/geocode', params, method='GET')
            return response
            
        except Exception as e:
            logger.error(f"Erro na geocodificação: {str(e)}")
            return {'error': f'Erro na geocodificação: {str(e)}'}
    
    @classmethod
    def verificar_status_flask(cls) -> Dict[str, Any]:
        """
        Verifica se o serviço Flask está funcionando
        
        Returns:
            Status do serviço Flask
        """
        try:
            response = cls._make_request('/health', method='GET')
            return {
                'status': 'online',
                'flask_response': response
            }
            
        except Exception as e:
            logger.error(f"Flask service offline: {str(e)}")
            return {
                'status': 'offline',
                'error': str(e)
            }
    
    @classmethod
    def _make_request(cls, endpoint: str, data: Optional[Dict] = None, method: str = 'POST') -> Any:
        """
        Faz requisição para o Flask
        
        Args:
            endpoint: Endpoint do Flask
            data: Dados para enviar
            method: Método HTTP
            
        Returns:
            Resposta do Flask
        """
        url = f"{cls.FLASK_BASE_URL}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=data, timeout=cls.TIMEOUT)
            else:
                response = requests.post(url, json=data, timeout=cls.TIMEOUT)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception("Serviço Flask não está disponível")
        except requests.exceptions.Timeout:
            raise Exception("Timeout na comunicação com Flask")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Erro HTTP do Flask: {e}")
        except Exception as e:
            raise Exception(f"Erro na comunicação com Flask: {e}")
    
    @classmethod
    def _save_temp_file(cls, uploaded_file: UploadedFile) -> str:
        """
        Salva arquivo temporariamente para análise
        
        Args:
            uploaded_file: Arquivo enviado
            
        Returns:
            Caminho do arquivo temporário
        """
        # Criar diretório temporário se não existir
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_verificacao')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        import uuid
        temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Salvar arquivo
        with open(temp_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        return temp_path
    
    @classmethod
    def _cleanup_temp_file(cls, temp_path: str):
        """
        Remove arquivo temporário
        
        Args:
            temp_path: Caminho do arquivo temporário
        """
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário {temp_path}: {e}")
    
    @classmethod
    def _get_file_extension(cls, filename: str) -> str:
        """
        Obtém extensão do arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Extensão do arquivo
        """
        return filename.split('.')[-1].lower() if '.' in filename else ''

class VerificadorIntegrationManager:
    """Gerenciador de integração entre Django e Flask"""
    
    @classmethod
    def processar_upload_arquivo(cls, uploaded_file: UploadedFile, company: Company, user: CustomUser) -> Dict[str, Any]:
        """
        Processa upload de arquivo completo
        
        Args:
            uploaded_file: Arquivo enviado
            company: Empresa do usuário
            user: Usuário que fez o upload
            
        Returns:
            Resultado completo do processamento
        """
        try:
            # 1. Criar registro no banco Django
            cto_file = CTOMapFile.objects.create(
                file=uploaded_file,
                description=f"Análise de {uploaded_file.name}",
                company=company,
                uploaded_by=user,
                is_processed=False
            )
            
            # 2. Verificar se Flask está online
            flask_status = VerificadorFlaskService.verificar_status_flask()
            if flask_status['status'] != 'online':
                return {
                    'success': False,
                    'error': 'Serviço de verificação temporariamente indisponível',
                    'cto_file_id': cto_file.id,
                    'flask_status': flask_status
                }
            
            # 3. Processar arquivo no Flask
            flask_result = VerificadorFlaskService.verificar_arquivo(uploaded_file, company, user)
            
            # 4. Atualizar registro Django com resultado
            if flask_result.get('success'):
                cto_file.is_processed = True
                cto_file.processed_at = timezone.now()
                
                # Salvar dados do resultado (pode ser expandido)
                cto_file.description = f"Análise concluída - {flask_result.get('results', {}).get('viability_score', 'N/A')} pontos"
                cto_file.save()
            
            return {
                'success': flask_result.get('success', False),
                'cto_file_id': cto_file.id,
                'flask_result': flask_result,
                'flask_status': flask_status
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento completo: {str(e)}")
            return {
                'success': False,
                'error': f'Erro no processamento: {str(e)}'
            }
    
    @classmethod
    def obter_estatisticas_integracao(cls) -> Dict[str, Any]:
        """
        Obtém estatísticas da integração
        
        Returns:
            Estatísticas da integração
        """
        try:
            # Status do Flask
            flask_status = VerificadorFlaskService.verificar_status_flask()
            
            # Estatísticas Django
            total_files = CTOMapFile.objects.count()
            processed_files = CTOMapFile.objects.filter(is_processed=True).count()
            
            # Arquivos disponíveis no Flask
            flask_files = VerificadorFlaskService.listar_arquivos_disponiveis()
            
            return {
                'flask_status': flask_status,
                'django_stats': {
                    'total_files': total_files,
                    'processed_files': processed_files,
                    'processing_rate': (processed_files / total_files * 100) if total_files > 0 else 0
                },
                'flask_files_count': len(flask_files),
                'integration_active': flask_status['status'] == 'online'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'error': str(e),
                'integration_active': False
            }
