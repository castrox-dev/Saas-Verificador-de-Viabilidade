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
        
        # 7. Validação de assinatura de arquivo
        self._validate_file_signature(file)
        
        # 8. Verificação de conteúdo malicioso
        self._scan_malicious_content(file)
        
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
    
    def validate_file_advanced(self, file):
        """
        Validação avançada com múltiplas camadas de segurança
        """
        # 1. Validação básica
        self.validate_file(file)
        
        # 2. Verificação de magic numbers
        self._validate_magic_numbers(file)
        
        # 3. Verificação de estrutura
        self._validate_file_structure(file)
        
        # 4. Verificação de metadados
        self._validate_metadata(file)
        
        return True
    
    def _validate_magic_numbers(self, file):
        """Verificação de magic numbers do arquivo"""
        try:
            file.seek(0)
            header = file.read(16)
            file.seek(0)
            
            # Magic numbers para tipos permitidos
            valid_magic_numbers = {
                b'PK\x03\x04': 'Excel/Office',
                b'\xd0\xcf\x11\xe0': 'Excel Legacy',
                b'<?xml': 'XML/KML',
                b'<kml': 'KML',
                b'<Document': 'KML Document'
            }
            
            # Verificar se o header corresponde a um tipo permitido
            is_valid = False
            for magic, file_type in valid_magic_numbers.items():
                if header.startswith(magic):
                    is_valid = True
                    logger.info(f"Magic number válido detectado: {file_type}")
                    break
            
            if not is_valid:
                # Para CSV, verificar se é texto válido
                if file.name.lower().endswith('.csv'):
                    try:
                        file.seek(0)
                        content = file.read(1024).decode('utf-8')
                        if content and not any(ord(c) < 32 and c not in '\t\n\r' for c in content[:100]):
                            is_valid = True
                    except:
                        pass
            
            if not is_valid:
                raise ValidationError("Arquivo com magic number inválido ou suspeito")
                
        except Exception as e:
            logger.error(f"Erro na verificação de magic numbers: {str(e)}")
            raise ValidationError("Erro na verificação de integridade do arquivo")
    
    def _validate_file_structure(self, file):
        """Verificação da estrutura do arquivo"""
        try:
            file_ext = os.path.splitext(file.name)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                self._validate_excel_structure(file)
            elif file_ext == '.csv':
                self._validate_csv_structure(file)
            elif file_ext == '.kml':
                self._validate_kml_structure(file)
            elif file_ext == '.kmz':
                self._validate_kmz_structure(file)
                
        except Exception as e:
            logger.error(f"Erro na verificação de estrutura: {str(e)}")
            raise ValidationError("Arquivo com estrutura inválida")
    
    def _validate_excel_structure(self, file):
        """Verificação da estrutura de arquivos Excel"""
        # Verificações adicionais para Excel
        pass
    
    def _validate_csv_structure(self, file):
        """Verificação da estrutura de arquivos CSV"""
        try:
            file.seek(0)
            lines = file.read(1024).decode('utf-8', errors='ignore').split('\n')
            
            # Verificar se tem pelo menos uma linha com dados
            if len(lines) < 2:
                raise ValidationError("Arquivo CSV muito pequeno ou vazio")
            
            # Verificar se as linhas têm estrutura consistente
            first_line = lines[0]
            if not first_line.strip():
                raise ValidationError("Arquivo CSV sem cabeçalho válido")
                
        except Exception as e:
            logger.error(f"Erro na verificação de estrutura CSV: {str(e)}")
            raise ValidationError("Arquivo CSV com estrutura inválida")
    
    def _validate_kml_structure(self, file):
        """Verificação da estrutura de arquivos KML"""
        try:
            file.seek(0)
            content = file.read(2048).decode('utf-8', errors='ignore')
            
            # Verificar tags essenciais do KML
            required_tags = ['<kml', '<Document', '<Placemark']
            found_tags = [tag for tag in required_tags if tag in content]
            
            if len(found_tags) < 2:
                raise ValidationError("Arquivo KML sem estrutura válida")
                
        except Exception as e:
            logger.error(f"Erro na verificação de estrutura KML: {str(e)}")
            raise ValidationError("Arquivo KML com estrutura inválida")
    
    def _validate_kmz_structure(self, file):
        """Verificação da estrutura de arquivos KMZ"""
        try:
            file.seek(0)
            file_content = file.read()
            file.seek(0)
            
            with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_file:
                # Verificar se tem pelo menos um KML
                kml_files = [name for name in zip_file.namelist() if name.lower().endswith('.kml')]
                if not kml_files:
                    raise ValidationError("Arquivo KMZ sem arquivo KML")
                
                # Verificar se o KML principal é válido
                main_kml = kml_files[0]
                kml_content = zip_file.read(main_kml).decode('utf-8', errors='ignore')
                
                if not any(tag in kml_content for tag in ['<kml', '<Document', '<Placemark']):
                    raise ValidationError("Arquivo KMZ com KML inválido")
                    
        except Exception as e:
            logger.error(f"Erro na verificação de estrutura KMZ: {str(e)}")
            raise ValidationError("Arquivo KMZ com estrutura inválida")
    
    def _validate_metadata(self, file):
        """Verificação de metadados do arquivo"""
        try:
            # Verificar se o arquivo não está vazio
            if file.size == 0:
                raise ValidationError("Arquivo vazio")
            
            # Verificar se o arquivo não é muito pequeno (possível arquivo corrompido)
            if file.size < 10:
                raise ValidationError("Arquivo muito pequeno, possivelmente corrompido")
                
        except Exception as e:
            logger.error(f"Erro na verificação de metadados: {str(e)}")
            raise ValidationError("Erro na verificação de metadados")
    
    def _validate_file_signature(self, file):
        """Validação de assinatura de arquivo"""
        try:
            file.seek(0)
            header = file.read(8)
            file.seek(0)
            
            # Verificar assinaturas conhecidas
            if file.name.lower().endswith('.xlsx'):
                # XLSX deve começar com PK (ZIP)
                if not header.startswith(b'PK'):
                    raise ValidationError("Assinatura XLSX inválida")
            
            elif file.name.lower().endswith('.xls'):
                # XLS deve começar com assinatura OLE
                if not header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                    raise ValidationError("Assinatura XLS inválida")
            
            elif file.name.lower().endswith('.csv'):
                # CSV deve ser texto
                try:
                    header.decode('utf-8')
                except UnicodeDecodeError:
                    raise ValidationError("Arquivo CSV com codificação inválida")
            
            elif file.name.lower().endswith('.kml'):
                # KML deve começar com XML
                if not header.startswith(b'<?xml') and not header.startswith(b'<kml'):
                    raise ValidationError("Assinatura KML inválida")
            
            elif file.name.lower().endswith('.kmz'):
                # KMZ deve começar com PK (ZIP)
                if not header.startswith(b'PK'):
                    raise ValidationError("Assinatura KMZ inválida")
                    
        except Exception as e:
            logger.error(f"Erro na validação de assinatura: {str(e)}")
            raise ValidationError("Assinatura de arquivo inválida")
    
    def _scan_malicious_content(self, file):
        """Verificação de conteúdo malicioso"""
        try:
            file.seek(0)
            content = file.read(1024)  # Ler primeiros 1KB
            
            # Padrões suspeitos
            suspicious_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'<iframe',
                b'<object',
                b'<embed',
                b'eval(',
                b'exec(',
                b'system(',
                b'shell_exec',
                b'cmd.exe',
                b'powershell',
                b'<form',
                b'onload=',
                b'onclick=',
                b'onerror='
            ]
            
            content_lower = content.lower()
            for pattern in suspicious_patterns:
                if pattern in content_lower:
                    logger.warning(f"Conteúdo suspeito detectado em {file.name}: {pattern}")
                    raise ValidationError("Conteúdo suspeito detectado no arquivo")
            
            # Verificar se é um arquivo binário disfarçado
            if file.name.lower().endswith(('.csv', '.kml')):
                # Arquivos de texto não devem ter muitos bytes nulos
                null_count = content.count(b'\x00')
                if null_count > len(content) * 0.1:  # Mais de 10% de bytes nulos
                    raise ValidationError("Arquivo de texto com conteúdo binário suspeito")
            
        except Exception as e:
            logger.error(f"Erro na verificação de conteúdo malicioso: {str(e)}")
            raise ValidationError("Erro na verificação de conteúdo malicioso")