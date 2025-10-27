from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import os

class Company(models.Model):
    """Modelo para representar as empresas clientes"""
    name = models.CharField(max_length=200, verbose_name="Nome da Empresa")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug", help_text="URL amigável para a empresa")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    email = models.EmailField(verbose_name="E-mail da Empresa")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    address = models.TextField(blank=True, verbose_name="Endereço")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Garantir que o slug seja único
            original_slug = self.slug
            counter = 1
            while Company.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    """Modelo customizado de usuário com roles e empresa"""
    
    USER_ROLES = [
        ('RM', 'Administrador RM'),  # Você e o Bone
        ('COMPANY_ADMIN', 'Administrador da Empresa'),  # Admin da empresa cliente
        ('COMPANY_USER', 'Usuário da Empresa'),  # Usuário comum da empresa
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=USER_ROLES, 
        default='COMPANY_USER',
        verbose_name="Função"
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='users',
        verbose_name="Empresa"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Superusuários não precisam seguir as regras de empresa
        if self.is_superuser:
            return
            
        # RM admins não precisam de empresa
        if self.role == 'RM' and self.company:
            raise ValidationError("Administradores RM não devem ter empresa associada.")
        
        # Outros roles precisam de empresa
        if self.role in ['COMPANY_ADMIN', 'COMPANY_USER'] and not self.company:
            raise ValidationError("Usuários de empresa devem ter uma empresa associada.")

    def save(self, *args, **kwargs):
        self.clean()
        # Garantir separação de privilégios entre RM e empresas
        if self.role == 'RM':
            # RM não deve ter empresa associada
            self.company_id = None
            # RM pode acessar áreas administrativas do sistema
            if not self.is_staff:
                self.is_staff = True
            # Não forçamos superuser aqui; fica a cargo de seed/gestão
        else:
            # Usuários de empresas nunca devem ser superuser, nem staff global
            if self.is_superuser:
                self.is_superuser = False
            if self.is_staff:
                self.is_staff = False
        super().save(*args, **kwargs)

    @property
    def is_rm_admin(self):
        """Verifica se é administrador RM"""
        return self.role == 'RM' or self.is_superuser

    @property
    def is_company_admin(self):
        """Verifica se é administrador da empresa"""
        return self.role == 'COMPANY_ADMIN'

    @property
    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.is_rm_admin or self.is_company_admin

    @property
    def can_upload_maps(self):
        """Verifica se pode fazer upload de mapas"""
        return self.is_rm_admin or self.role in ['COMPANY_ADMIN', 'COMPANY_USER']

    def get_full_name(self):
        """Retorna nome completo ou username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __str__(self):
        if self.company:
            return f"{self.get_full_name() or self.username} - {self.company.name}"
        return self.get_full_name() or self.username

class CTOMapFile(models.Model):
    """Modelo para arquivos de mapas CTO"""
    
    FILE_TYPES = [
        ('kml', 'KML'),
        ('kmz', 'KMZ'),
        ('csv', 'CSV'),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    file = models.FileField(upload_to="cto_maps/", verbose_name="Arquivo")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='csv', verbose_name="Tipo de Arquivo")
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='cto_maps',
        verbose_name="Empresa"
    )
    uploaded_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='uploaded_maps',
        verbose_name="Enviado por"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Enviado em")
    
    # Status de processamento
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS, 
        default='pending',
        verbose_name="Status de Processamento"
    )
    is_processed = models.BooleanField(default=False, verbose_name="Processado")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Processado em")
    
    # Resultados da análise Flask
    analysis_id = models.CharField(max_length=100, blank=True, verbose_name="ID da Análise")
    viability_score = models.IntegerField(null=True, blank=True, verbose_name="Score de Viabilidade")
    processing_time = models.FloatField(null=True, blank=True, verbose_name="Tempo de Processamento (s)")
    
    # Dados da análise (JSON)
    analysis_results = models.JSONField(default=dict, blank=True, verbose_name="Resultados da Análise")
    issues_found = models.JSONField(default=list, blank=True, verbose_name="Problemas Encontrados")
    recommendations = models.JSONField(default=list, blank=True, verbose_name="Recomendações")
    
    # Metadados do arquivo
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="Tamanho do Arquivo (bytes)")
    coordinates_count = models.IntegerField(null=True, blank=True, verbose_name="Número de Coordenadas")
    
    # Campos de auditoria
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Mapa CTO"
        verbose_name_plural = "Mapas CTO"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'processing_status']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
            models.Index(fields=['file_type', 'is_processed']),
        ]

    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Verificar se o usuário pode fazer upload
        if self.uploaded_by and not self.uploaded_by.can_upload_maps:
            raise ValidationError("Usuário não tem permissão para fazer upload de mapas.")
        
        # Verificar se o usuário pertence à empresa
        if self.uploaded_by and self.company and self.uploaded_by.company != self.company:
            raise ValidationError("Usuário não pertence à empresa especificada.")
        
        # Determinar tipo de arquivo automaticamente
        if self.file and not self.file_type:
            file_name = self.file.name.lower()
            if file_name.endswith('.kml'):
                self.file_type = 'kml'
            elif file_name.endswith('.kmz'):
                self.file_type = 'kmz'
            elif file_name.endswith('.csv'):
                self.file_type = 'csv'
            elif file_name.endswith('.xls'):
                self.file_type = 'xls'
            elif file_name.endswith('.xlsx'):
                self.file_type = 'xlsx'
    
    def save(self, *args, **kwargs):
        self.clean()
        
        # Calcular tamanho do arquivo
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                pass
        
        super().save(*args, **kwargs)
    
    def get_file_size_mb(self):
        """Retorna o tamanho do arquivo em MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_viability_status(self):
        """Retorna o status de viabilidade baseado no score"""
        if self.viability_score is None:
            return "Não analisado"
        
        if self.viability_score >= 80:
            return "Viável"
        elif self.viability_score >= 60:
            return "Viabilidade Limitada"
        else:
            return "Sem Viabilidade"
    
    def get_viability_color(self):
        """Retorna a cor do status de viabilidade"""
        if self.viability_score is None:
            return "#6c757d"  # Cinza
        
        if self.viability_score >= 80:
            return "#28a745"  # Verde
        elif self.viability_score >= 60:
            return "#ffc107"  # Amarelo
        else:
            return "#dc3545"  # Vermelho
    
    @property
    def file_name(self):
        """Retorna apenas o nome do arquivo"""
        return os.path.basename(self.file.name) if self.file else ""

    def __str__(self):
        return f"{self.description or os.path.basename(self.file.name)} - {self.company.name}"
