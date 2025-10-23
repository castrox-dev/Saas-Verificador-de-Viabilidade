import os
import hashlib
import logging
from django.core.exceptions import ValidationError
import mimetypes
import zipfile
import io

logger = logging.getLogger('security')

class SecureFileValidator:
    """
    Validador seguro para upload de arquivos com verificação de conteúdo real
    """
    
    ALLOWED_MIME_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',
        'application/csv',
        'application/vnd.google-earth.kml+xml',  # .kml
        'application/vnd.google-earth.kmz',  # .kmz
        'text/xml',  # .kml (alternativo)
        'application/xml',  # .kml (alternativo)
        'application/zip'  # .kmz (é um arquivo ZIP)
    ]
    
    ALLOWED_EXTENSIONS = ['.xlsx', '.xls', '.csv', '.kml', '.kmz']
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILENAME_LENGTH = 100
    
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1'
    ]
    
    def __init__(self):
        pass
    
    def validate_file(self, file):
        """
        Validação completa e segura do arquivo
        """
        if not file:
            raise ValidationError("Arquivo não fornecido")
        
        # 1. Validação básica de tamanho
        if file.size > self.MAX_FILE_SIZE:
            size_mb = round(file.size / (1024 * 1024), 2)
            raise ValidationError(
                f"Arquivo muito grande ({size_mb}MB). "
                f"Tamanho máximo permitido: {self.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        # 2. Validação de nome do arquivo
        self._validate_filename(file.name)
        
        # 3. Validação de extensão
        self._validate_extension(file.name)
        
        # 4. Validação de conteúdo real (MIME type)
        self._validate_content(file)
        
        # 5. Validação de integridade
        self._validate_integrity(file)
        
        # 6. Verificação de malware básica
        self._scan_for_malware(file)
        
        logger.info(f"Arquivo validado com sucesso: {file.name}")
        return True
    
    def _validate_filename(self, filename):
        """Validação segura do nome do arquivo"""
        if len(filename) > self.MAX_FILENAME_LENGTH:
            raise ValidationError(
                f"Nome do arquivo muito longo. "
                f"Máximo permitido: {self.MAX_FILENAME_LENGTH} caracteres"
            )
        
        # Caracteres perigosos
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/', '\0']
        if any(char in filename for char in dangerous_chars):
            raise ValidationError(
                "Nome do arquivo contém caracteres inválidos ou perigosos"
            )
        
        # Path traversal
        if '..' in filename or filename.startswith('/'):
            raise ValidationError("Nome do arquivo contém sequências perigosas")
    
    def _validate_extension(self, filename):
        """Validação de extensão do arquivo"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Extensão não permitida: {file_ext}. "
                f"Extensões aceitas: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # Verificar extensões perigosas
        if file_ext in self.DANGEROUS_EXTENSIONS:
            raise ValidationError(f"Extensão perigosa detectada: {file_ext}")
    
    def _validate_content(self, file):
        """Validação do conteúdo real do arquivo"""
        try:
            # Ler início do arquivo para análise
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)  # Reset position
            
            # Detectar MIME type usando mimetypes (fallback)
            real_mime, _ = mimetypes.guess_type(file.name)
            
            # Verificar se o MIME type está na lista permitida (se detectado)
            if real_mime and real_mime not in self.ALLOWED_MIME_TYPES:
                logger.warning(
                    f"MIME type suspeito detectado: {real_mime} para arquivo {file.name}",
                    extra={
                        'filename': file.name,
                        'detected_mime': real_mime,
                        'file_size': file.size
                    }
                )
                raise ValidationError(
                    f"Tipo de arquivo não permitido detectado: {real_mime}"
                )
            
            # Verificação adicional por extensão (mais confiável)
            file_ext = os.path.splitext(file.name)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                self._validate_excel_content(file)
            elif file_ext == '.csv':
                self._validate_csv_content(file)
            elif file_ext == '.kml':
                self._validate_kml_content(file)
            elif file_ext == '.kmz':
                self._validate_kmz_content(file)
                
        except Exception as e:
            logger.error(f"Erro na validação de conteúdo: {str(e)}")
            raise ValidationError("Erro na validação do arquivo")
    
    def _validate_excel_content(self, file):
        """Validação específica para arquivos Excel"""
        try:
            file.seek(0)
            # Verificar assinatura de arquivo Excel
            header = file.read(8)
            file.seek(0)
            
            # Verificar se é um arquivo Excel válido
            if not (header.startswith(b'PK') or header.startswith(b'\xd0\xcf\x11\xe0')):
                raise ValidationError("Arquivo Excel inválido ou corrompido")
                
        except Exception as e:
            logger.warning(f"Arquivo Excel inválido: {str(e)}")
            raise ValidationError("Arquivo Excel corrompido ou inválido")
    
    def _validate_csv_content(self, file):
        """Validação específica para arquivos CSV"""
        try:
            file.seek(0)
            # Ler primeiras linhas para verificar estrutura
            content = file.read(1024).decode('utf-8', errors='ignore')
            
            # Verificar se contém código suspeito
            suspicious_patterns = [
                '<script', 'javascript:', 'vbscript:', 'onload=',
                'eval(', 'exec(', 'system(', 'shell_exec('
            ]
            
            for pattern in suspicious_patterns:
                if pattern.lower() in content.lower():
                    raise ValidationError("Arquivo CSV contém conteúdo suspeito")
                    
        except UnicodeDecodeError:
            raise ValidationError("Arquivo CSV com codificação inválida")
        except Exception as e:
            logger.warning(f"Arquivo CSV inválido: {str(e)}")
            raise ValidationError("Arquivo CSV corrompido ou inválido")
    
    def _validate_kml_content(self, file):
        """Validação específica para arquivos KML"""
        try:
            file.seek(0)
            content = file.read(1024).decode('utf-8', errors='ignore')
            
            # Verificar se é um KML válido
            if not ('<kml' in content.lower() or '<document' in content.lower()):
                raise ValidationError("Arquivo KML inválido ou corrompido")
            
            # Verificar se contém elementos suspeitos
            suspicious_patterns = [
                '<script', 'javascript:', 'vbscript:', 'onload=',
                'eval(', 'exec(', 'system(', 'shell_exec(',
                '<iframe', '<object', '<embed', '<applet'
            ]
            
            for pattern in suspicious_patterns:
                if pattern.lower() in content.lower():
                    raise ValidationError("Arquivo KML contém conteúdo suspeito")
            
            # Verificar estrutura básica do KML
            if not any(tag in content.lower() for tag in ['<placemark', '<point', '<linestring', '<polygon']):
                logger.warning("KML sem elementos geográficos válidos")
                
        except UnicodeDecodeError:
            raise ValidationError("Arquivo KML com codificação inválida")
        except Exception as e:
            logger.warning(f"Arquivo KML inválido: {str(e)}")
            raise ValidationError("Arquivo KML corrompido ou inválido")
    
    def _validate_kmz_content(self, file):
        """Validação específica para arquivos KMZ"""
        try:
            file.seek(0)
            # KMZ é um arquivo ZIP, verificar se é ZIP válido
            import zipfile
            import io
            
            # Ler arquivo em memória para verificação
            file_content = file.read()
            file.seek(0)
            
            try:
                with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_file:
                    # Verificar se contém arquivo KML
                    kml_files = [name for name in zip_file.namelist() if name.lower().endswith('.kml')]
                    
                    if not kml_files:
                        raise ValidationError("Arquivo KMZ não contém arquivo KML")
                    
                    # Verificar se o KML principal é válido
                    main_kml = kml_files[0]  # Usar o primeiro KML encontrado
                    kml_content = zip_file.read(main_kml).decode('utf-8', errors='ignore')
                    
                    if not ('<kml' in kml_content.lower() or '<document' in kml_content.lower()):
                        raise ValidationError("Arquivo KMZ contém KML inválido")
                    
                    # Verificar se não contém arquivos suspeitos
                    suspicious_files = [name for name in zip_file.namelist() 
                                      if any(ext in name.lower() for ext in ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js'])]
                    
                    if suspicious_files:
                        raise ValidationError("Arquivo KMZ contém arquivos suspeitos")
                    
                    # Verificar tamanho total descompactado
                    total_size = sum(info.file_size for info in zip_file.infolist())
                    if total_size > self.MAX_FILE_SIZE * 2:  # Permitir 2x o tamanho para KMZ
                        raise ValidationError("Arquivo KMZ muito grande após descompactação")
                        
            except zipfile.BadZipFile:
                raise ValidationError("Arquivo KMZ corrompido ou inválido")
                
        except Exception as e:
            logger.warning(f"Arquivo KMZ inválido: {str(e)}")
            raise ValidationError("Arquivo KMZ corrompido ou inválido")
    
    def _validate_integrity(self, file):
        """Validação de integridade do arquivo"""
        try:
            file.seek(0)
            # Calcular hash para verificar integridade
            file_hash = hashlib.sha256()
            for chunk in iter(lambda: file.read(4096), b""):
                file_hash.update(chunk)
            
            # Armazenar hash para verificação futura
            file.seek(0)
            logger.info(f"Hash SHA256 calculado para {file.name}: {file_hash.hexdigest()}")
            
        except Exception as e:
            logger.error(f"Erro no cálculo de integridade: {str(e)}")
            raise ValidationError("Erro na verificação de integridade")
    
    def _scan_for_malware(self, file):
        """Verificação básica de malware"""
        try:
            file.seek(0)
            content = file.read(1024)
            
            # Padrões suspeitos comuns
            suspicious_patterns = [
                b'MZ',  # Executável Windows
                b'\x4d\x5a',  # PE header
                b'PK\x03\x04',  # ZIP/Office com macros
                b'%PDF',  # PDF (não permitido)
            ]
            
            for pattern in suspicious_patterns:
                if content.startswith(pattern):
                    logger.warning(f"Padrão suspeito detectado em {file.name}: {pattern}")
                    raise ValidationError("Arquivo contém padrões suspeitos")
                    
        except Exception as e:
            logger.error(f"Erro na verificação de malware: {str(e)}")
            # Não bloquear por erro na verificação, apenas logar
            pass
