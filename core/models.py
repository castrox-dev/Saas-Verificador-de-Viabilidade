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
        super().save(*args, **kwargs)

    @property
    def is_rm_admin(self):
        """Verifica se é administrador RM"""
        return self.role == 'RM'

    @property
    def is_company_admin(self):
        """Verifica se é administrador da empresa"""
        return self.role == 'COMPANY_ADMIN'

    @property
    def is_company_user(self):
        """Verifica se é usuário comum da empresa"""
        return self.role == 'COMPANY_USER'

    @property
    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.role in ['RM', 'COMPANY_ADMIN']

    @property
    def can_upload_maps(self):
        """Verifica se pode fazer upload de mapas"""
        return self.role in ['RM', 'COMPANY_ADMIN']

    def __str__(self):
        if self.company:
            return f"{self.get_full_name() or self.username} - {self.company.name}"
        return self.get_full_name() or self.username

class CTOMapFile(models.Model):
    """Modelo para arquivos de mapas CTO"""
    file = models.FileField(upload_to="cto_maps/", verbose_name="Arquivo")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
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
    is_processed = models.BooleanField(default=False, verbose_name="Processado")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Processado em")

    class Meta:
        verbose_name = "Mapa CTO"
        verbose_name_plural = "Mapas CTO"
        ordering = ['-uploaded_at']

    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Verificar se o usuário pode fazer upload
        if self.uploaded_by and not self.uploaded_by.can_upload_maps:
            raise ValidationError("Usuário não tem permissão para fazer upload de mapas.")
        
        # Verificar se a empresa do usuário coincide com a empresa do mapa
        if (self.uploaded_by and self.uploaded_by.company and 
            self.company and self.uploaded_by.company != self.company):
            raise ValidationError("Usuário só pode fazer upload para sua própria empresa.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file.name} - {self.company.name}"

    @property
    def file_name(self):
        return os.path.basename(self.file.name)
