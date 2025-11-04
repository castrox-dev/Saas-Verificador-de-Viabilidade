from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
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
rm_admin_required = user_passes_test(lambda u: is_rm_admin(u) or u.is_superuser, login_url='/rm/login/')
company_admin_required = user_passes_test(
    lambda u: is_rm_admin(u) or is_company_admin(u) or u.is_superuser,
    login_url='/rm/login/'
)

user_management_required = user_passes_test(lambda u: can_manage_users(u) or u.is_superuser, login_url='/rm/login/')
# map_upload_required removido - funcionalidade de upload foi consolidada


def company_access_required(require_admin=False, allow_user_role=True):
    """
    Decorator que garante acesso multi-tenant por slug de empresa.
    - RM admins e superusers sempre têm acesso.
    - Caso contrário, o usuário deve pertencer à empresa do slug.
    - Se require_admin=True, o usuário também deve ser COMPANY_ADMIN.
    - Se allow_user_role=False, COMPANY_USER não pode acessar (exceto verificador).
    Respostas padrão: 403 HTML.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            # Acesso amplo para RM/superuser
            if user.is_authenticated and (getattr(user, 'is_rm_admin', False) or getattr(user, 'is_superuser', False)):
                return view_func(request, *args, **kwargs)
            # Buscar empresa pelo slug
            company_slug = kwargs.get('company_slug')
            if not user.is_authenticated or not company_slug:
                raise PermissionDenied
            # Import lazy para evitar ciclos
            from .models import Company
            try:
                company = Company.objects.get(slug=company_slug)
            except Company.DoesNotExist:
                raise PermissionDenied
            # Verificação de pertencimento
            if not user.company or user.company != company:
                return HttpResponseForbidden()
            
            # COMPANY_USER só pode acessar verificador e upload
            if user.role == 'COMPANY_USER' and not allow_user_role:
                # Redirecionar para verificador se tentar acessar outras páginas
                from django.shortcuts import redirect
                return redirect('company:ftth_viewer:index', company_slug=company_slug)
            
            # Se requer admin, validar
            if require_admin and not getattr(user, 'is_company_admin', False):
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def company_access_required_json(require_admin=False):
    """
    Variante para endpoints JSON/AJAX.
    - Responde com JsonResponse(status=403) quando sem permissão.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            # Acesso amplo para RM/superuser
            if user.is_authenticated and (getattr(user, 'is_rm_admin', False) or getattr(user, 'is_superuser', False)):
                return view_func(request, *args, **kwargs)
            company_slug = kwargs.get('company_slug')
            if not user.is_authenticated or not company_slug:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            from .models import Company
            try:
                company = Company.objects.get(slug=company_slug)
            except Company.DoesNotExist:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            if not user.company or user.company != company:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            if require_admin and not getattr(user, 'is_company_admin', False):
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def same_company_required(view_func):
    """Mantido por compatibilidade; use company_access_required(False)."""
    return company_access_required(require_admin=False)(view_func)


class SameCompanyRequiredMixin:
    """Mixin que verifica se o usuário pode acessar dados da empresa"""
    def dispatch(self, request, *args, **kwargs):
        # Para uso futuro com CBVs
        return super().dispatch(request, *args, **kwargs)

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