from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps

def is_rm_admin(user):
    """Verifica se o usuário é administrador RM"""
    return user.is_authenticated and user.is_rm_admin

def is_company_admin(user):
    """Verifica se o usuário é administrador da empresa"""
    return user.is_authenticated and user.is_company_admin

def is_company_user(user):
    """Verifica se o usuário é usuário da empresa"""
    return user.is_authenticated and user.is_company_user

def can_manage_users(user):
    """Verifica se o usuário pode gerenciar outros usuários"""
    return user.is_authenticated and user.can_manage_users

def can_upload_maps(user):
    """Verifica se o usuário pode fazer upload de mapas"""
    return user.is_authenticated and user.can_upload_maps

def belongs_to_same_company(user, target_user):
    """Verifica se dois usuários pertencem à mesma empresa"""
    if user.is_rm_admin:
        return True  # RM admins podem acessar qualquer empresa
    
    if not user.company or not target_user.company:
        return False
    
    return user.company == target_user.company

# Decorators para views usando user_passes_test
rm_admin_required = user_passes_test(is_rm_admin, login_url='/login/')
company_admin_required = user_passes_test(
    lambda u: is_rm_admin(u) or is_company_admin(u), 
    login_url='/login/'
)

user_management_required = user_passes_test(can_manage_users, login_url='/login/')
map_upload_required = user_passes_test(can_upload_maps, login_url='/login/')

def same_company_required(view_func):
    """Decorator que verifica se o usuário pode acessar dados da empresa"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Este decorator deve ser usado em conjunto com outros que passam
        # o objeto target_user ou company como parâmetro
        return view_func(request, *args, **kwargs)
    return wrapper

# Mixins para Class-Based Views
class RMAdminRequiredMixin:
    """Mixin que exige que o usuário seja administrador RM"""
    
    def dispatch(self, request, *args, **kwargs):
        if not is_rm_admin(request.user):
            raise PermissionDenied("Acesso restrito a administradores RM.")
        return super().dispatch(request, *args, **kwargs)

class CompanyAdminRequiredMixin:
    """Mixin que exige que o usuário seja administrador da empresa"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (is_rm_admin(request.user) or is_company_admin(request.user)):
            raise PermissionDenied("Acesso restrito a administradores.")
        return super().dispatch(request, *args, **kwargs)

class UserManagementRequiredMixin:
    """Mixin que exige permissão para gerenciar usuários"""
    
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_users(request.user):
            raise PermissionDenied("Você não tem permissão para gerenciar usuários.")
        return super().dispatch(request, *args, **kwargs)

class MapUploadRequiredMixin:
    """Mixin que exige permissão para upload de mapas"""
    
    def dispatch(self, request, *args, **kwargs):
        if not can_upload_maps(request.user):
            raise PermissionDenied("Você não tem permissão para fazer upload de mapas.")
        return super().dispatch(request, *args, **kwargs)

class SameCompanyRequiredMixin:
    """Mixin que verifica se o usuário pode acessar dados da empresa"""
    
    def dispatch(self, request, *args, **kwargs):
        # Implementação específica deve ser feita nas views que herdam este mixin
        return super().dispatch(request, *args, **kwargs)