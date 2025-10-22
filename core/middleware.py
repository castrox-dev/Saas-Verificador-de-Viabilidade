from django.shortcuts import get_object_or_404
from django.http import Http404
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from .models import Company
import re

class CompanyMiddleware(MiddlewareMixin):
    """
    Middleware para detectar a empresa pela URL e adicionar ao request
    URLs suportadas:
    - /rm/... -> Acesso RM Systems
    - /{company_slug}/... -> Acesso específico da empresa
    """
    
    def process_request(self, request):
        # Extrair o primeiro segmento da URL
        path = request.path.strip('/')
        segments = path.split('/') if path else []
        
        # Inicializar variáveis
        request.company = None
        request.company_slug = None
        request.is_rm_access = False
        
        if not segments:
            # URL raiz - redirecionar para RM
            request.is_rm_access = True
            return None
            
        first_segment = segments[0].lower()
        
        # Verificar se é acesso RM
        if first_segment == 'rm':
            request.is_rm_access = True
            return None
            
        # Verificar se é acesso de empresa
        # Buscar empresa pelo nome (slug)
        try:
            # Converter nome da empresa para slug (remover espaços, caracteres especiais)
            company_slug = first_segment.replace('-', ' ').replace('_', ' ')
            
            # Buscar empresa por nome (case insensitive)
            company = Company.objects.filter(
                name__iexact=company_slug,
                is_active=True
            ).first()
            
            if not company:
                # Tentar buscar por slug mais flexível
                companies = Company.objects.filter(is_active=True)
                for comp in companies:
                    comp_slug = self.create_slug(comp.name)
                    if comp_slug == first_segment:
                        company = comp
                        break
            
            if company:
                request.company = company
                request.company_slug = first_segment
                return None
            else:
                # Empresa não encontrada - pode ser uma URL normal
                # Deixar passar para o Django resolver
                return None
                
        except Exception:
            # Em caso de erro, deixar passar
            return None
    
    def create_slug(self, name):
        """Criar slug a partir do nome da empresa"""
        if not name:
            return ''
        
        # Converter para minúsculas
        slug = name.lower()
        
        # Remover acentos e caracteres especiais
        slug = re.sub(r'[àáâãäå]', 'a', slug)
        slug = re.sub(r'[èéêë]', 'e', slug)
        slug = re.sub(r'[ìíîï]', 'i', slug)
        slug = re.sub(r'[òóôõö]', 'o', slug)
        slug = re.sub(r'[ùúûü]', 'u', slug)
        slug = re.sub(r'[ç]', 'c', slug)
        slug = re.sub(r'[ñ]', 'n', slug)
        
        # Substituir espaços e caracteres especiais por hífen
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        
        # Remover hífens do início e fim
        slug = slug.strip('-')
        
        return slug