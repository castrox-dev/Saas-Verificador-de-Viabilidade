from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden, HttpResponse, Http404, JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db import transaction
import logging
import os

from .forms import CTOMapFileForm, CompanyForm, CustomUserForm
from .models import CTOMapFile, Company, CustomUser
from .permissions import (
    is_rm_admin, is_company_admin, can_manage_users,
    rm_admin_required, user_management_required, map_upload_required
)

# Configurar logging
logger = logging.getLogger(__name__)


def login_view(request):
    """View para login de usuários"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('rm:admin_dashboard')
        else:
            messages.error(request, 'Credenciais inválidas.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """View para logout de usuários"""
    logout(request)
    return redirect('rm:login')

@login_required
def dashboard(request):
    """Dashboard principal baseado no role do usuário"""
    context = {
        'user': request.user,
        'is_rm_admin': request.user.is_rm_admin,
        'is_company_admin': request.user.is_company_admin,
        'is_company_user': request.user.is_company_user,
    }
    
    if request.user.is_rm_admin:
        context['companies'] = Company.objects.all()
        context['total_users'] = CustomUser.objects.count()
        context['total_maps'] = CTOMapFile.objects.count()
    elif request.user.company:
        context['company'] = request.user.company
        context['company_users'] = CustomUser.objects.filter(company=request.user.company)
        context['company_maps'] = CTOMapFile.objects.filter(company=request.user.company)

    if request.method == "POST":
        form = CTOMapFileForm(request.POST, request.FILES)
        
        try:
            if form.is_valid():
                with transaction.atomic():
                    uploaded_file = form.save()
                    
                    # Log da ação
                    logger.info(f"Arquivo {uploaded_file.file.name} enviado por {request.user.username}")
                    
                    # Mensagem de sucesso detalhada
                    file_size = round(uploaded_file.file.size / 1024, 2)  # KB
                    messages.success(
                        request, 
                        f"✅ Arquivo '{uploaded_file.file.name}' enviado com sucesso! "
                        f"Tamanho: {file_size} KB"
                    )
                    
                return redirect("rm:admin_dashboard")
            else:
                # Processar erros específicos do formulário
                error_messages = []
                
                for field, errors in form.errors.items():
                    if field == 'file':
                        for error in errors:
                            error_messages.append(f"📁 Arquivo: {error}")
                    elif field == 'description':
                        for error in errors:
                            error_messages.append(f"📝 Descrição: {error}")
                    else:
                        for error in errors:
                            error_messages.append(f"⚠️ {error}")
                
                # Adicionar todas as mensagens de erro
                for error_msg in error_messages:
                    messages.error(request, error_msg)
                
                logger.warning(f"Erro de validação no upload por {request.user.username}: {form.errors}")
                
        except ValidationError as e:
            messages.error(request, f"❌ Erro de validação: {str(e)}")
            logger.error(f"Erro de validação: {str(e)}")
            
        except Exception as e:
            messages.error(
                request, 
                "❌ Erro interno do servidor. Tente novamente ou contate o suporte."
            )
            logger.error(f"Erro inesperado no upload: {str(e)}")
            
    else:
        form = CTOMapFileForm()

    # Buscar arquivos com informações adicionais
    try:
        files = CTOMapFile.objects.order_by("-uploaded_at")
        
        # Adicionar estatísticas
        total_files = files.count()
        total_size = sum(f.file.size for f in files if f.file)
        total_size_mb = round(total_size / (1024 * 1024), 2)
        
        context = {
            'form': form,
            'files': files,
            'stats': {
                'total_files': total_files,
                'total_size_mb': total_size_mb,
                'recent_uploads': files[:5]  # 5 uploads mais recentes
            }
        }
        
    except Exception as e:
        messages.error(request, "❌ Erro ao carregar arquivos. Tente recarregar a página.")
        logger.error(f"Erro ao buscar arquivos: {str(e)}")
        context = {'form': form, 'files': [], 'stats': {'total_files': 0, 'total_size_mb': 0}}

    return render(request, "dashboard.html", context)


@login_required
def download_file(request, file_id):
    """View para download de arquivos com validações"""
    if not request.user.is_superuser:
        messages.error(request, "Acesso negado para download.")
        return redirect("rm:admin_dashboard")
    
    try:
        file_obj = get_object_or_404(CTOMapFile, id=file_id)
        
        if not file_obj.file or not os.path.exists(file_obj.file.path):
            messages.error(request, "❌ Arquivo não encontrado no servidor.")
            return redirect("rm:admin_dashboard")
        
        # Log do download
        logger.info(f"Download do arquivo {file_obj.file.name} por {request.user.username}")
        
        # Preparar resposta para download
        with open(file_obj.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_obj.file.name}"'
            
        messages.success(request, f"📥 Download de '{file_obj.file.name}' iniciado.")
        return response
        
    except Exception as e:
        messages.error(request, "❌ Erro ao baixar arquivo. Tente novamente.")
        logger.error(f"Erro no download: {str(e)}")
        return redirect("rm:admin_dashboard")


@login_required
def delete_file(request, file_id):
    """View para exclusão de arquivos com confirmação"""
    if not request.user.is_superuser:
        messages.error(request, "Acesso negado para exclusão.")
        return redirect("rm:admin_dashboard")
    
    try:
        file_obj = get_object_or_404(CTOMapFile, id=file_id)
        file_name = file_obj.file.name
        
        # Remover arquivo físico se existir
        if file_obj.file and os.path.exists(file_obj.file.path):
            os.remove(file_obj.file.path)
        
        # Remover registro do banco
        file_obj.delete()
        
        # Log da exclusão
        logger.info(f"Arquivo {file_name} excluído por {request.user.username}")
        
        messages.success(request, f"🗑️ Arquivo '{file_name}' excluído com sucesso.")
        
    except Exception as e:
        messages.error(request, "❌ Erro ao excluir arquivo. Tente novamente.")
        logger.error(f"Erro na exclusão: {str(e)}")
    
    return redirect("rm:admin_dashboard")


def home(request):
    """Página inicial - redireciona para dashboard se logado"""
    if request.user.is_authenticated:
        return redirect('rm:admin_dashboard')
    return render(request, 'home.html')

# Views para gerenciamento de empresas (apenas RM admins)
@login_required
@rm_admin_required
def company_list(request):
    """Lista todas as empresas (apenas RM admins)"""
    companies = Company.objects.all()
    return render(request, 'companies/list.html', {'companies': companies})

@login_required
@rm_admin_required
def company_create(request):
    """Cria uma nova empresa (apenas RM admins)"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'Empresa {company.name} criada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm()
    
    return render(request, 'companies/form.html', {'form': form, 'title': 'Criar Empresa'})

@login_required
@rm_admin_required
def company_edit(request, company_id):
    """Edita uma empresa (apenas RM admins)"""
    company = get_object_or_404(Company, id=company_id)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f'Empresa {company.name} atualizada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'companies/form.html', {'form': form, 'title': 'Editar Empresa'})

# Views para gerenciamento de usuários
@login_required
@user_management_required
def user_list(request):
    """Lista usuários baseado no role"""
    if request.user.is_rm_admin:
        users = CustomUser.objects.all()
    elif request.user.is_company_admin:
        users = CustomUser.objects.filter(company=request.user.company)
    else:
        raise PermissionDenied
    
    return render(request, 'users/list.html', {'users': users})

@login_required
@user_management_required
def user_create(request):
    """Cria um novo usuário"""
    if request.method == 'POST':
        form = CustomUserForm(request.POST, current_user=request.user)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                
                # Se é admin da empresa, associa à sua empresa
                if request.user.is_company_admin and not request.user.is_rm_admin:
                    user.company = request.user.company
                
                user.save()
                messages.success(request, f'Usuário {user.username} criado com sucesso!')
                return redirect('rm:user_list')
    else:
        form = CustomUserForm(current_user=request.user)
    
    return render(request, 'users/form.html', {'form': form, 'title': 'Criar Usuário'})

@login_required
@user_management_required
def user_edit(request, user_id):
    """Edita um usuário"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Verifica se o usuário pode editar este usuário específico
    if request.user.is_company_admin and user.company != request.user.company:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuário {user.username} atualizado com sucesso!')
            return redirect('rm:user_list')
    else:
        form = CustomUserForm(instance=user, current_user=request.user)
    
    return render(request, 'users/form.html', {'form': form, 'title': 'Editar Usuário'})

# Views para mapas CTO
@login_required
def map_list(request):
    """Lista mapas CTO baseado no role"""
    if request.user.is_rm_admin:
        maps = CTOMapFile.objects.all()
    elif request.user.company:
        maps = CTOMapFile.objects.filter(company=request.user.company)
    else:
        maps = CTOMapFile.objects.none()
    
    return render(request, 'maps/list.html', {'maps': maps})

@login_required
@map_upload_required
def map_upload(request):
    """Upload de mapa CTO"""
    
    if request.method == 'POST':
        form = CTOMapFileForm(request.POST, request.FILES)
        if form.is_valid():
            map_file = form.save(commit=False)
            map_file.uploaded_by = request.user
            
            # Se não é RM admin, associa à empresa do usuário
            if not request.user.is_rm_admin:
                map_file.company = request.user.company
            
            map_file.save()
            messages.success(request, 'Mapa CTO enviado com sucesso!')
            return redirect('rm:map_list')
    else:
        form = CTOMapFileForm()
    
    return render(request, 'maps/upload.html', {'form': form})

# Views AJAX para toggle de status
@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Ativa/desativa um usuário via AJAX"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Verifica permissões
    if not request.user.can_manage_users():
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    if request.user.is_company_admin and user.company != request.user.company:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Usuário {"ativado" if user.is_active else "desativado"} com sucesso!'
    })

@login_required
@require_http_methods(["POST"])
def toggle_company_status(request, company_id):
    """Ativa/desativa uma empresa via AJAX (apenas RM admins)"""
    if not request.user.is_rm_admin:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    company = get_object_or_404(Company, id=company_id)
    company.is_active = not company.is_active
    company.save()
    
    return JsonResponse({
        'success': True,
        'is_active': company.is_active,
        'message': f'Empresa {"ativada" if company.is_active else "desativada"} com sucesso!'
    })


# ===== VIEWS MULTI-TENANT =====

def home_redirect(request):
    """Redireciona da raiz para RM"""
    return redirect('/rm/login/')


# ===== VIEWS RM SYSTEMS =====

def rm_login_view(request):
    """View de login específica para RM Systems"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'RM':
            login(request, user)
            return redirect('rm:admin_dashboard')
        else:
            messages.error(request, 'Credenciais inválidas.')
    
    return render(request, 'login.html')

@login_required
@rm_admin_required
def rm_admin_dashboard(request):
    """Dashboard administrativo RM"""
    companies = Company.objects.all()
    total_users = CustomUser.objects.count()
    total_maps = CTOMapFile.objects.count()
    
    context = {
        'companies': companies,
        'total_companies': companies.count(),
        'total_users': total_users,
        'total_maps': total_maps,
    }
    return render(request, 'core/rm_dashboard.html', context)

@login_required
@rm_admin_required
def rm_company_list(request):
    """Lista de empresas para RM"""
    companies = Company.objects.all()
    return render(request, 'core/rm_companies.html', {'companies': companies})

@login_required
@rm_admin_required
def rm_company_create(request):
    """Criar nova empresa"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa criada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm()
    
    return render(request, 'rm/companies/form.html', {'form': form, 'action': 'Criar'})

@login_required
@rm_admin_required
def rm_company_edit(request, pk):
    """Editar empresa"""
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'rm/companies/form.html', {'form': form, 'action': 'Editar'})

@login_required
@rm_admin_required
@require_http_methods(["POST"])
def rm_company_toggle(request, pk):
    """Toggle status da empresa"""
    company = get_object_or_404(Company, pk=pk)
    company.is_active = not company.is_active
    company.save()
    
    return JsonResponse({
        'success': True,
        'is_active': company.is_active,
        'message': f'Empresa {"ativada" if company.is_active else "desativada"} com sucesso!'
    })

@login_required
@rm_admin_required
def rm_user_list(request):
    """Lista global de usuários para RM"""
    users = CustomUser.objects.select_related('company').all()
    return render(request, 'rm/users/list.html', {'users': users})

@login_required
@rm_admin_required
def rm_user_create(request):
    """Criar novo usuário (RM view)"""
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('rm:user_list')
    else:
        form = CustomUserForm()
    
    return render(request, 'rm/users/form.html', {'form': form, 'action': 'Criar'})

@login_required
@rm_admin_required
def rm_user_edit(request, pk):
    """Editar usuário (RM view)"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('rm:user_list')
    else:
        form = CustomUserForm(instance=user)
    
    return render(request, 'rm/users/form.html', {'form': form, 'action': 'Editar'})

@login_required
@rm_admin_required
@require_http_methods(["POST"])
def rm_user_toggle(request, pk):
    """Toggle status do usuário"""
    user = get_object_or_404(CustomUser, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Usuário {"ativado" if user.is_active else "desativado"} com sucesso!'
    })

@login_required
@rm_admin_required
def rm_map_list(request):
    """Lista global de mapas para RM"""
    maps = CTOMapFile.objects.select_related('company', 'uploaded_by').all()
    return render(request, 'rm/maps/list.html', {'maps': maps})

@login_required
@rm_admin_required
def rm_map_download(request, pk):
    """Download de mapa (RM view)"""
    map_file = get_object_or_404(CTOMapFile, pk=pk)
    
    if os.path.exists(map_file.file.path):
        with open(map_file.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{map_file.file_name}"'
            return response
    else:
        raise Http404("Arquivo não encontrado")

@login_required
@rm_admin_required
@require_http_methods(["POST"])
def rm_map_delete(request, pk):
    """Deletar mapa (RM view)"""
    map_file = get_object_or_404(CTOMapFile, pk=pk)
    
    try:
        if os.path.exists(map_file.file.path):
            os.remove(map_file.file.path)
        map_file.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Mapa deletado com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao deletar mapa: {str(e)}'
        })

@login_required
@rm_admin_required
def rm_reports(request):
    """Relatórios e estatísticas para RM"""
    context = {
        'total_companies': Company.objects.count(),
        'active_companies': Company.objects.filter(is_active=True).count(),
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'total_maps': CTOMapFile.objects.count(),
        'companies_with_maps': Company.objects.filter(ctomapfile__isnull=False).distinct().count(),
    }
    return render(request, 'rm/reports.html', context)


# ===== VIEWS EMPRESA =====

def company_login_view(request, company_slug):
    """View de login específica para empresa"""
    try:
        company = Company.objects.get(slug=company_slug, is_active=True)
    except Company.DoesNotExist:
        messages.error(request, 'Empresa não encontrada ou inativa.')
        return redirect('home_redirect')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.company == company and user.is_active:
            login(request, user)
            
            # Redireciona baseado no role
            if user.role == 'COMPANY_ADMIN':
                return redirect('company:dashboard', company_slug=company_slug)
            else:
                return redirect('company:verificador', company_slug=company_slug)
        else:
            messages.error(request, 'Credenciais inválidas.')
    
    context = {
        'company': company,
    }
    return render(request, 'login.html', context)

@login_required
def company_dashboard(request, company_slug):
    """Dashboard da empresa (apenas admins)"""
    if request.user.role != 'COMPANY_ADMIN':
        return redirect('company:verificador', company_slug=company_slug)
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    users = CustomUser.objects.filter(company=company)
    maps = CTOMapFile.objects.filter(company=company)
    
    context = {
        'company': company,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'total_maps': maps.count(),
        'recent_maps': maps.order_by('-uploaded_at')[:5],
    }
    return render(request, 'core/company_dashboard.html', context)

@login_required
def company_verificador(request, company_slug):
    """Verificador da empresa (todos os usuários)"""
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    maps = CTOMapFile.objects.filter(company=company).order_by('-uploaded_at')
    
    context = {
        'company': company,
        'maps': maps,
    }
    return render(request, 'core/company_verifier.html', context)

@login_required
def company_user_list(request, company_slug):
    """Lista de usuários da empresa (apenas admins)"""
    if request.user.role != 'COMPANY_ADMIN':
        return HttpResponseForbidden()
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    users = CustomUser.objects.filter(company=company)
    return render(request, 'company/users/list.html', {'users': users, 'company': company})

@login_required
def company_user_create(request, company_slug):
    """Criar usuário da empresa (apenas admins)"""
    if request.user.role != 'COMPANY_ADMIN':
        return HttpResponseForbidden()
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.company = company
            user.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('company:user_list', company_slug=company_slug)
    else:
        form = CustomUserForm()
    
    return render(request, 'company/users/form.html', {'form': form, 'action': 'Criar', 'company': company})

@login_required
def company_user_edit(request, company_slug, pk):
    """Editar usuário da empresa (apenas admins)"""
    if request.user.role != 'COMPANY_ADMIN':
        return HttpResponseForbidden()
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    user = get_object_or_404(CustomUser, pk=pk, company=company)
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('company:user_list', company_slug=company_slug)
    else:
        form = CustomUserForm(instance=user)
    
    return render(request, 'company/users/form.html', {'form': form, 'action': 'Editar', 'company': company})

@login_required
@require_http_methods(["POST"])
def company_user_toggle(request, company_slug, pk):
    """Toggle status do usuário da empresa"""
    if request.user.role != 'COMPANY_ADMIN':
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    user = get_object_or_404(CustomUser, pk=pk, company=company)
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Usuário {"ativado" if user.is_active else "desativado"} com sucesso!'
    })

@login_required
def company_map_list(request, company_slug):
    """Lista de mapas da empresa (painel admin)"""
    if request.user.role != 'COMPANY_ADMIN':
        return HttpResponseForbidden()
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    maps = CTOMapFile.objects.filter(company=company)
    return render(request, 'company/maps/list.html', {'maps': maps, 'company': company})

@login_required
def company_map_upload(request, company_slug):
    """Upload de mapa da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = CTOMapFileForm(request.POST, request.FILES)
        if form.is_valid():
            map_file = form.save(commit=False)
            map_file.company = company
            map_file.uploaded_by = request.user
            map_file.save()
            messages.success(request, 'Mapa enviado com sucesso!')
            
            if request.user.role == 'COMPANY_ADMIN':
                return redirect('company:map_list', company_slug=company_slug)
            else:
                return redirect('company:verificador', company_slug=company_slug)
    else:
        form = CTOMapFileForm()
    
    return render(request, 'company/maps/upload.html', {'form': form, 'company': company})

@login_required
def company_map_download(request, company_slug, pk):
    """Download de mapa da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    map_file = get_object_or_404(CTOMapFile, pk=pk, company=company)
    
    if os.path.exists(map_file.file.path):
        with open(map_file.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{map_file.file_name}"'
            return response
    else:
        raise Http404("Arquivo não encontrado")

@login_required
@require_http_methods(["POST"])
def company_map_delete(request, company_slug, pk):
    """Deletar mapa da empresa"""
    if request.user.role != 'COMPANY_ADMIN':
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    map_file = get_object_or_404(CTOMapFile, pk=pk, company=company)
    
    try:
        if os.path.exists(map_file.file.path):
            os.remove(map_file.file.path)
        map_file.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Mapa deletado com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao deletar mapa: {str(e)}'
        })

@login_required
def company_map_history(request, company_slug):
    """Histórico de mapas da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    if request.user.company != company:
        return HttpResponseForbidden()
    
    maps = CTOMapFile.objects.filter(company=company).order_by('-uploaded_at')
    return render(request, 'company/maps/history.html', {'maps': maps, 'company': company})
