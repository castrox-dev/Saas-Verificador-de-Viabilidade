from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden, HttpResponse, Http404, JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
import logging
import os
import csv
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import CTOMapFileForm, CompanyForm, CustomUserForm, CustomUserChangeForm
from .models import CTOMapFile, Company, CustomUser
from .permissions import (
    is_rm_admin, is_company_admin, can_manage_users,
    rm_admin_required, user_management_required, map_upload_required, company_access_required, company_access_required_json
)
from .rate_limiting import login_rate_limit, upload_rate_limit, general_rate_limit

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
def login_view(request):
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('rm:login')


@login_required
def company_logout_view(request, company_slug):
    logout(request)
    return redirect('company:login', company_slug=company_slug)


def home_redirect(request):
    return redirect('/rm/login/')


@ensure_csrf_cookie
@login_rate_limit
def rm_login_view(request):
    if request.method == 'POST':
        input_id = (request.POST.get('username', '') or '').strip()
        password = (request.POST.get('password', '') or '').strip()
        # aceitar e-mail ou username
        username = input_id
        if input_id and '@' in input_id:
            try:
                u = CustomUser.objects.get(email__iexact=input_id)
                username = u.username
            except CustomUser.DoesNotExist:
                username = input_id
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_rm_admin or user.is_superuser):
            login(request, user)
            return redirect('rm:admin_dashboard')
        messages.error(request, 'Credenciais inválidas.')
    return render(request, 'login.html')


@login_required
@rm_admin_required
def company_list(request):
    qs = Company.objects.all().order_by('name')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(cnpj__icontains=q) | Q(email__icontains=q))
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    companies = paginator.get_page(page_number)
    return render(request, 'core/rm_companies.html', {'companies': companies, 'q': q})


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
def rm_company_portal(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    users_qs = CustomUser.objects.filter(company=company)
    maps_qs = CTOMapFile.objects.filter(company=company)
    context = {
        'company': company,
        'total_users': users_qs.count(),
        'active_users': users_qs.filter(is_active=True).count(),
        'total_maps': maps_qs.count(),
        'recent_maps': maps_qs.order_by('-uploaded_at')[:5],
    }
    return render(request, 'core/rm_company_portal.html', context)


@login_required
@rm_admin_required
def rm_company_login_check(request, company_slug):
    if request.user.is_authenticated and request.user.is_rm_admin:
        return redirect('rm:company_portal', company_slug=company_slug)
    return redirect('rm:login')


@login_required
@rm_admin_required
def rm_user_list(request):
    q = request.GET.get('q', '').strip()
    users = CustomUser.objects.all().select_related('company').order_by('username')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    return render(request, 'rm/users/list.html', {'users': users, 'q': q})


@login_required
@rm_admin_required
def rm_user_create(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                messages.success(request, 'Usuário criado com sucesso!')
                return redirect('rm:user_list')
    else:
        form = CustomUserForm()
    return render(request, 'rm/users/form.html', {'form': form})


@login_required
@rm_admin_required
def rm_user_delete(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Não permitir deletar superusuários
            if user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível deletar superusuários.'
                }, status=400)
            
            # Não permitir deletar o próprio usuário
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível deletar seu próprio usuário.'
                }, status=400)
            
            username = user.username
            user.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Usuário {username} deletado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao deletar usuário: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido.'
    }, status=405)


@login_required
@rm_admin_required
def rm_user_edit(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                messages.success(request, 'Usuário atualizado com sucesso!')
                return redirect('rm:user_list')
    else:
        form = CustomUserChangeForm(instance=user_obj)
    return render(request, 'rm/users/form.html', {'form': form, 'user_obj': user_obj})


@login_rate_limit
def company_login_view(request, company_slug):
    context = {'company_slug': company_slug}
    if request.method == 'POST':
        input_id = (request.POST.get('username', '') or '').strip()
        password = (request.POST.get('password', '') or '').strip()
        # aceitar e-mail ou username
        username = input_id
        if input_id and '@' in input_id:
            try:
                u = CustomUser.objects.get(email__iexact=input_id)
                username = u.username
            except CustomUser.DoesNotExist:
                username = input_id
        
        user = authenticate(request, username=username, password=password)
        
        # Debug logging
        logger.info(f"Login attempt for company: {company_slug}, input: {input_id}, resolved username: {username}")
        if user:
            logger.info(f"User found: {user.username}, company: {user.company}, is_active: {user.is_active}")
            if user.company:
                logger.info(f"User company slug: {user.company.slug}")
            else:
                logger.info("User has no company associated")
        else:
            logger.info("Authentication failed")
        
        if user is not None and user.company and user.company.slug == company_slug:
            login(request, user)
            logger.info(f"Login successful, redirecting to dashboard for {company_slug}")
            return redirect('company:dashboard', company_slug=company_slug)
        else:
            logger.info("Login failed: user not found, no company, or wrong company")
            messages.error(request, 'Credenciais inválidas para esta empresa.')
    return render(request, 'company/login.html', context)


@login_required
@company_access_required(require_admin=False)
def company_dashboard(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    
    # Debug logging
    logger.info(f"Dashboard access for company: {company_slug}")
    logger.info(f"User: {request.user.username}, Company: {request.user.company}, Role: {request.user.role}")
    
    # Redirecionar usuários comuns para o mapa CTO
    if request.user.role == 'COMPANY_USER':
        return redirect('company:mapa_cto', company_slug=company_slug)
    
    users_qs = CustomUser.objects.filter(company=company)
    maps_qs = CTOMapFile.objects.filter(company=company)
    context = {
        'company': company,
        'total_users': users_qs.count(),
        'active_users': users_qs.filter(is_active=True).count(),
        'total_maps': maps_qs.count(),
    }
    return render(request, 'core/company_dashboard.html', context)


@login_required
@company_access_required(require_admin=False)
def company_verificador(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    form = CTOMapFileForm()
    maps = CTOMapFile.objects.filter(company=company).order_by('-uploaded_at')[:10]
    context = {
        'company': company,
        'form': form,
        'maps': maps,
    }
    return render(request, 'core/company_verifier.html', context)


@login_required
@company_access_required(require_admin=False)
def company_mapa_cto(request, company_slug):
    """Página do mapa CTO para usuários comuns da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    context = {
        'company': company,
    }
    return render(request, 'company/mapa_cto.html', context)


@login_required
@company_access_required(require_admin=False)
def company_user_list(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    users = CustomUser.objects.filter(company=company).order_by('username')
    return render(request, 'company/users/list.html', {'users': users, 'company': company})


@login_required
@company_access_required(require_admin=True)
def company_map_list(request, company_slug):
    """Lista de mapas da empresa (painel admin)"""
    if not (request.user.is_company_admin or request.user.is_rm_admin or request.user.is_superuser):
        return HttpResponseForbidden()
    company = get_object_or_404(Company, slug=company_slug)
    if not (request.user.is_rm_admin or request.user.is_superuser) and request.user.company != company:
        return HttpResponseForbidden()

    maps = CTOMapFile.objects.filter(company=company)
    return render(request, 'company/maps/list.html', {'maps': maps, 'company': company})


@login_required
@company_access_required(require_admin=True)
@upload_rate_limit
def company_map_upload(request, company_slug):
    """Upload de mapa da empresa (apenas admins)"""
    if not (request.user.is_company_admin or request.user.is_rm_admin or request.user.is_superuser):
        return HttpResponseForbidden()
    company = get_object_or_404(Company, slug=company_slug)
    if not (request.user.is_rm_admin or request.user.is_superuser) and request.user.company != company:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = CTOMapFileForm(request.POST, request.FILES)
        if form.is_valid():
            map_file = form.save(commit=False)
            map_file.company = company
            map_file.uploaded_by = request.user
            map_file.save()
            messages.success(request, 'Mapa enviado com sucesso!')
            return redirect('company:map_list', company_slug=company_slug)
    else:
        form = CTOMapFileForm()
    return render(request, 'company/maps/upload.html', {'form': form, 'company': company})


@login_required
@rm_admin_required
def rm_company_map_upload(request, company_slug):
    """Upload de mapa para empresa (RM)"""
    company = get_object_or_404(Company, slug=company_slug)
    if request.method == 'POST':
        form = CTOMapFileForm(request.POST, request.FILES)
        if form.is_valid():
            map_file = form.save(commit=False)
            # Força associação à empresa do slug
            map_file.company = company
            map_file.uploaded_by = request.user
            map_file.save()
            messages.success(request, 'Mapa enviado com sucesso!')
            return redirect('rm:map_by_company')
    else:
        # Pré-seleciona a empresa e opcionalmente poderíamos ocultar o campo no template
        form = CTOMapFileForm(initial={'company': company})
    return render(request, 'rm/maps/upload_company.html', {'form': form, 'company': company})


@login_required
@company_access_required(require_admin=False)
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
@company_access_required_json(require_admin=True)
@require_http_methods(["POST"])
def company_map_delete(request, company_slug, pk):
    """Deletar mapa da empresa"""
    if not (request.user.is_company_admin or request.user.is_rm_admin or request.user.is_superuser):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    company = get_object_or_404(Company, slug=company_slug)
    map_file = get_object_or_404(CTOMapFile, pk=pk, company=company)
    try:
        if map_file.file and os.path.exists(map_file.file.path):
            os.remove(map_file.file.path)
        map_file.delete()
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Falha ao excluir'}, status=500)


@login_required
@company_access_required(require_admin=False)
def company_map_history(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    maps = CTOMapFile.objects.filter(company=company).order_by('-uploaded_at')
    return render(request, 'company/maps/history.html', {'maps': maps, 'company': company})


@login_required
@rm_admin_required
def rm_user_quick_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        messages.warning(request, 'Digite e-mail, nome ou usuário para buscar.')
        return redirect('rm:user_list')
    # Preferir correspondências exatas de e-mail ou username
    exact_qs = CustomUser.objects.filter(Q(email__iexact=q) | Q(username__iexact=q))
    if exact_qs.count() == 1:
        return redirect('rm:user_edit', user_id=exact_qs.first().pk)
    # Fallback para busca parcial em nome, username ou e-mail
    qs = CustomUser.objects.filter(
        Q(email__icontains=q) |
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q)
    ).order_by('username')
    if qs.count() == 1:
        return redirect('rm:user_edit', user_id=qs.first().pk)
    if qs.exists():
        messages.info(request, f'{qs.count()} usuários encontrados para "{q}". Refine a busca.')
        return redirect(f"{reverse('rm:user_list')}?q={q}")
    messages.warning(request, f'Nenhum usuário encontrado para "{q}".')
    return redirect(f"{reverse('rm:user_list')}?q={q}")


@login_required
@rm_admin_required
def rm_maps_by_company(request):
    """Visão RM: Mapas agrupados por empresa, com ações e gráficos"""
    companies = Company.objects.all().order_by('name')
    company_stats = []
    for c in companies:
        maps_qs = CTOMapFile.objects.filter(company=c)
        stats = {
            'company': c,
            'maps': maps_qs.select_related('company', 'uploaded_by'),
            'total_maps': maps_qs.count(),
            'processed_maps': maps_qs.filter(is_processed=True).count(),
            'pending_maps': maps_qs.filter(is_processed=False).count(),
        }
        company_stats.append(stats)

    # Dados agregados para gráficos gerais (total de mapas por empresa)
    labels = [s['company'].name for s in company_stats]
    totals = [s['total_maps'] for s in company_stats]
    processed = [s['processed_maps'] for s in company_stats]
    pending = [s['pending_maps'] for s in company_stats]

    context = {
        'companies': companies,
        'company_stats': company_stats,
        'chart_labels': labels,
        'chart_totals': totals,
        'chart_processed': processed,
        'chart_pending': pending,
    }
    return render(request, 'rm/maps/by_company.html', context)


@login_required
@company_access_required(require_admin=True)
def company_map_admin(request, company_slug):
    """Tela de administração avançada de mapas para empresa"""
    if not (request.user.is_company_admin or request.user.is_rm_admin or request.user.is_superuser):
        return HttpResponseForbidden()

    company = get_object_or_404(Company, slug=company_slug)
    if not (request.user.is_rm_admin or request.user.is_superuser) and request.user.company != company:
        return HttpResponseForbidden()

    # Buscar todos os mapas da empresa
    maps = CTOMapFile.objects.filter(company=company).select_related('uploaded_by').order_by('-uploaded_at')

    # Calcular estatísticas
    total_maps = maps.count()
    processed_maps = maps.filter(is_processed=True).count()
    pending_maps = maps.filter(is_processed=False).count()

    # Calcular tamanho total dos arquivos
    total_size = sum(map_file.file.size for map_file in maps if map_file.file)
    total_size_mb = round(total_size / (1024 * 1024), 2)

    context = {
        'company': company,
        'maps': maps,
        'total_maps': total_maps,
        'processed_maps': processed_maps,
        'pending_maps': pending_maps,
        'total_size_mb': total_size_mb,
    }

    return render(request, 'company/maps/admin.html', context)


# --- Novas views RM para relatórios e lista/ações de mapas ---
@login_required
@rm_admin_required
def rm_map_list(request):
    """Lista de todos os mapas (visão RM), com filtro por empresa via ?company=slug"""
    company_slug = request.GET.get('company')
    maps = CTOMapFile.objects.all().select_related('company', 'uploaded_by').order_by('-uploaded_at')
    if company_slug:
        maps = maps.filter(company__slug=company_slug)
    return render(request, 'rm/maps/list.html', {'maps': maps})


@login_required
@rm_admin_required
def rm_map_download(request, pk):
    map_file = get_object_or_404(CTOMapFile, pk=pk)
    if os.path.exists(map_file.file.path):
        with open(map_file.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{map_file.file_name}"'
            return response
    raise Http404('Arquivo não encontrado')


@login_required
@rm_admin_required
@require_http_methods(["POST"])
def rm_map_delete(request, pk):
    map_file = get_object_or_404(CTOMapFile, pk=pk)
    try:
        if map_file.file and os.path.exists(map_file.file.path):
            os.remove(map_file.file.path)
        map_file.delete()
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Falha ao excluir'}, status=500)


@login_required
@rm_admin_required
def rm_reports(request):
    companies = Company.objects.all().order_by('name')
    users = CustomUser.objects.all()

    # Estatísticas por empresa para gráficos
    company_stats = []
    for c in companies:
        maps_qs = CTOMapFile.objects.filter(company=c)
        company_stats.append({
            'company': c,
            'total_maps': maps_qs.count(),
            'processed_maps': maps_qs.filter(is_processed=True).count(),
            'pending_maps': maps_qs.filter(is_processed=False).count(),
        })

    labels = [s['company'].name for s in company_stats]
    totals = [s['total_maps'] for s in company_stats]
    processed = [s['processed_maps'] for s in company_stats]
    pending = [s['pending_maps'] for s in company_stats]

    # Totais gerais para o gráfico de status e cards
    overall_processed = CTOMapFile.objects.filter(is_processed=True).count()
    overall_pending = CTOMapFile.objects.filter(is_processed=False).count()

    context = {
        'total_companies': companies.count(),
        'active_companies': companies.filter(is_active=True).count(),
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'total_maps': CTOMapFile.objects.count(),
        'overall_processed': overall_processed,
        'overall_pending': overall_pending,
        'chart_labels': labels,
        'chart_totals': totals,
        'chart_processed': processed,
        'chart_pending': pending,
    }
    return render(request, 'rm/reports.html', context)


@login_required
@rm_admin_required
def rm_reports_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorios_rm.csv"'
    writer = csv.writer(response)
    writer.writerow(['Métrica', 'Valor'])
    writer.writerow(['Empresas (ativas)', Company.objects.filter(is_active=True).count()])
    writer.writerow(['Empresas (total)', Company.objects.count()])
    writer.writerow(['Usuários (ativos)', CustomUser.objects.filter(is_active=True).count()])
    writer.writerow(['Usuários (total)', CustomUser.objects.count()])
    writer.writerow(['Mapas CTO (total)', CTOMapFile.objects.count()])
    return response


# Redireciona para o dashboard correto conforme o papel do usuário

def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('rm:login')

    user = request.user
    if user.is_rm_admin or user.is_superuser:
        return redirect('rm:admin_dashboard')

    if user.company:
        if user.role == 'COMPANY_ADMIN':
            return redirect('company:dashboard', company_slug=user.company.slug)
        return redirect('company:mapa_cto', company_slug=user.company.slug)

    # Fallback: se não houver empresa associada, enviar para RM dashboard
    return redirect('rm:admin_dashboard')


@login_required
@rm_admin_required
def rm_company_create(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa criada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm()
    return render(request, 'rm/companies/form.html', {'form': form})


@login_required
@rm_admin_required
def rm_company_edit(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('rm:company_list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'rm/companies/form.html', {'form': form, 'company': company})


@login_required
@company_access_required(require_admin=True)
def company_user_create(request, company_slug):
    company = get_object_or_404(Company, slug=company_slug)
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.company = company
                # Papel padrão para criação pela empresa
                if not getattr(user, 'role', None):
                    user.role = 'COMPANY_USER'
                if user.role == 'RM':
                    messages.error(request, 'Não é possível criar usuário RM pela empresa.')
                else:
                    user.save()
                    messages.success(request, 'Usuário criado com sucesso!')
                    return redirect('company:user_list', company_slug=company_slug)
    else:
        form = CustomUserForm()
    return render(request, 'company/users/form.html', {'form': form, 'company': company})


@login_required
@company_access_required(require_admin=True)
def company_user_edit(request, company_slug, user_id):
    company = get_object_or_404(Company, slug=company_slug)
    user_obj = get_object_or_404(CustomUser, id=user_id, company=company)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.company = company  # força permanência na empresa
                if user.role == 'RM':
                    messages.error(request, 'Não é possível definir papel RM para usuário da empresa.')
                else:
                    user.save()
                    messages.success(request, 'Usuário atualizado com sucesso!')
                    return redirect('company:user_list', company_slug=company_slug)
    else:
        form = CustomUserChangeForm(instance=user_obj)
    return render(request, 'company/users/form.html', {'form': form, 'company': company, 'user_obj': user_obj})


@login_required
@company_access_required_json(require_admin=True)
@require_http_methods(["POST"])
def company_user_toggle(request, company_slug, user_id):
    try:
        target = get_object_or_404(CustomUser, id=user_id)
        # Bloquear operações perigosas
        if getattr(target, 'is_superuser', False) or getattr(target, 'is_rm_admin', False):
            return JsonResponse({'success': False, 'message': 'Operação não permitida para este usuário.'}, status=403)
        # Verificar pertencimento à mesma empresa
        if not target.company or target.company.slug != company_slug:
            return JsonResponse({'success': False, 'message': 'Usuário não pertence a esta empresa.'}, status=403)
        # Evitar auto-desativação
        if target.id == request.user.id:
            return JsonResponse({'success': False, 'message': 'Você não pode alterar seu próprio status.'}, status=400)
        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])
        return JsonResponse({'success': True, 'active': target.is_active})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Falha ao alterar status.'}, status=500)


@login_required
@rm_admin_required
@require_http_methods(["POST"])
def rm_company_delete(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    try:
        company.delete()
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Falha ao excluir empresa'}, status=500)
