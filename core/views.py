from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden, HttpResponse, Http404, JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
import logging
import os
import csv
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import CTOMapFileForm, CompanyForm, CustomUserForm, CustomUserChangeForm
from .models import CTOMapFile, Company, CustomUser
from .permissions import (
    is_rm_admin, is_company_admin, can_manage_users,
    rm_admin_required, user_management_required, company_access_required, company_access_required_json
)
from .reports import ReportGenerator, ExportManager
from .audit_logger import log_user_action, log_data_access
from .rate_limiting import login_rate_limit, upload_rate_limit, general_rate_limit
from .verificador_service import VerificadorService, VerificadorIntegrationManager

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
@cache_page(60 * 15)  # Cache por 15 minutos
def rm_admin_dashboard(request):
    """Dashboard administrativo RM com cache"""
    cache_key = f"rm_dashboard_{request.user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'core/rm_dashboard.html', cached_data)
    
    companies = Company.objects.all()
    total_users = CustomUser.objects.count()
    total_maps = CTOMapFile.objects.count()

    context = {
        'companies': companies,
        'total_companies': companies.count(),
        'total_users': total_users,
        'total_maps': total_maps,
    }
    
    # Cache por 15 minutos
    cache.set(cache_key, context, 60 * 15)
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
        
        # Debug logging (apenas em nível DEBUG para não expor informações sensíveis)
        logger.debug(f"Login attempt for company: {company_slug}")
        if user:
            logger.debug(f"User authentication successful for company: {company_slug}")
            if not user.company:
                logger.warning("User without company associated attempted login")
        else:
            logger.debug("Authentication failed - invalid credentials")
        
        if user is not None and user.company and user.company.slug == company_slug:
            login(request, user)
            # Log apenas sucesso sem informações sensíveis
            logger.info(f"Successful login for company: {company_slug}")
            # Redirecionar conforme o papel do usuário
            if user.role == 'COMPANY_ADMIN':
                return redirect('company:dashboard', company_slug=company_slug)
            elif user.role == 'COMPANY_USER':
                # Usuários comuns vão direto para o verificador
                return redirect(f'/{company_slug}/verificador/')
            else:
                # Fallback para verificador
                return redirect(f'/{company_slug}/verificador/')
        else:
            logger.warning(f"Failed login attempt for company: {company_slug} - invalid credentials or wrong company")
            messages.error(request, 'Credenciais inválidas para esta empresa.')
    return render(request, 'company/login.html', context)


@login_required
@company_access_required(require_admin=False, allow_user_role=False)
def company_dashboard(request, company_slug):
    """Dashboard - apenas para COMPANY_ADMIN e RM"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Debug logging (apenas em nível DEBUG para não expor informações sensíveis)
    logger.debug(f"Dashboard access - company: {company_slug}, user_id: {request.user.id}, role: {request.user.role}")
    
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
@company_access_required(require_admin=False, allow_user_role=True)
def company_verificador(request, company_slug):
    """Verificador - acessível para todos os usuários da empresa"""
    from django.shortcuts import redirect
    return redirect('verificador:index')


@login_required
@company_access_required(require_admin=False, allow_user_role=True)
def company_map_upload_page(request, company_slug):
    """Página de upload de mapas CTO"""
    import os
    company = get_object_or_404(Company, slug=company_slug)
    maps = CTOMapFile.objects.filter(company=company).order_by('-uploaded_at')[:20]
    
    # Adicionar informações de tamanho de arquivo com tratamento de erro
    for map in maps:
        try:
            if map.file and map.file.name:
                map.file_size_bytes = os.path.getsize(map.file.path) if os.path.exists(map.file.path) else None
                map.original_filename = os.path.basename(map.file.name)
            else:
                map.file_size_bytes = None
                map.original_filename = getattr(map, 'description', 'N/A')
        except (FileNotFoundError, ValueError, OSError):
            map.file_size_bytes = None
            map.original_filename = getattr(map, 'description', 'N/A')
    
    context = {
        'company': company,
        'maps': maps,
    }
    return render(request, 'core/upload_page.html', context)


@login_required
@company_access_required(require_admin=False)
@upload_rate_limit
def company_map_upload(request, company_slug):
    """Upload de mapa CTO via AJAX com verificação Flask"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    company = get_object_or_404(Company, slug=company_slug)
    
    try:
        # Verificar se o usuário pode fazer upload
        if not request.user.can_upload_maps:
            return JsonResponse({'success': False, 'message': 'Sem permissão para upload'}, status=403)
        
        # Verificar se o usuário pertence à empresa
        if request.user.company != company:
            return JsonResponse({'success': False, 'message': 'Acesso negado à empresa'}, status=403)
        
        # Verificar se há arquivo no request
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'message': 'Nenhum arquivo enviado'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Processar arquivo usando o verificador Flask
        result = VerificadorIntegrationManager.processar_upload_arquivo(
            uploaded_file=uploaded_file,
            company=company,
            user=request.user
        )
        
        if result['success']:
            # Log do upload bem-sucedido
            try:
                from .audit_logger import log_map_upload
                map_file = CTOMapFile.objects.get(id=result['cto_file_id'])
                log_map_upload(request.user, map_file, company)
            except Exception as log_error:
                logger.warning(f"Erro no log de upload: {str(log_error)}")
            
            # Preparar resposta com dados do Flask
            flask_result = result.get('flask_result', {})
            flask_data = flask_result.get('results', {})
            
            response_data = {
                'success': True,
                'message': 'Arquivo analisado com sucesso!',
                'file_id': result['cto_file_id'],
                'file_name': os.path.basename(uploaded_file.name),
                'analysis': {
                    'viability_score': flask_data.get('viability_score', 'N/A'),
                    'issues': flask_data.get('issues', []),
                    'recommendations': flask_data.get('recommendations', []),
                    'processing_time': flask_data.get('processing_time', 0),
                    'coordinates_count': flask_data.get('coordinates_count', 0)
                },
                'flask_status': result.get('flask_status', {})
            }
            
            return JsonResponse(response_data)
        else:
            # Upload falhou
            error_message = result.get('error', 'Erro desconhecido na análise')
            
            # Se o Flask estiver offline, ainda salvar o arquivo
            if result.get('flask_status', {}).get('status') != 'online':
                # Criar arquivo sem análise
                map_file = CTOMapFile(
                    file=uploaded_file,
                    description=request.POST.get('description', f'Arquivo enviado - Análise pendente'),
                    company=company,
                    uploaded_by=request.user,
                    processing_status='pending'
                )
                map_file.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Arquivo salvo. Análise será realizada quando o serviço estiver disponível.',
                    'file_id': map_file.id,
                    'file_name': os.path.basename(uploaded_file.name),
                    'analysis_pending': True,
                    'flask_status': result.get('flask_status', {})
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': error_message,
                    'flask_status': result.get('flask_status', {})
                }, status=400)
        
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Erro interno do servidor'}, status=500)


@login_required
@company_access_required(require_admin=False)
def company_verificar_coordenadas(request, company_slug):
    """Verifica viabilidade de coordenadas específicas"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    company = get_object_or_404(Company, slug=company_slug)
    
    try:
        # Verificar se o usuário pode fazer verificações
        if not request.user.can_upload_maps:
            return JsonResponse({'success': False, 'message': 'Sem permissão para verificação'}, status=403)
        
        # Obter coordenadas do request
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        
        if not lat or not lon:
            return JsonResponse({'success': False, 'message': 'Coordenadas não fornecidas'}, status=400)
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Coordenadas inválidas'}, status=400)
        
        # Verificar viabilidade usando Verificador Django
        result = VerificadorService.verificar_coordenadas(
            lat=lat,
            lon=lon,
            company=company,
            user=request.user
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': 'Verificação concluída',
                'analysis': result
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Erro na verificação'),
                'analysis': result
            }, status=400)
        
    except Exception as e:
        logger.error(f"Erro na verificação de coordenadas: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Erro interno do servidor'}, status=500)


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
@company_access_required(require_admin=True)
@require_http_methods(["POST"])
def company_map_delete(request, company_slug, pk):
    """Deletar mapa da empresa"""
    if not (request.user.is_company_admin or request.user.is_rm_admin or request.user.is_superuser):
        messages.error(request, 'Sem permissão para excluir arquivos')
        return redirect('company:upload', company_slug=company_slug)

    company = get_object_or_404(Company, slug=company_slug)
    map_file = get_object_or_404(CTOMapFile, pk=pk, company=company)
    
    try:
        # Remover arquivo físico se existir
        if map_file.file and os.path.exists(map_file.file.path):
            os.remove(map_file.file.path)
        
        # Deletar registro do banco
        map_file.delete()
        
        messages.success(request, 'Arquivo excluído com sucesso!')
        
    except Exception as e:
        logger.error(f"Erro ao excluir arquivo {pk}: {str(e)}")
        messages.error(request, 'Erro ao excluir arquivo. Tente novamente.')
    
    return redirect('company:upload', company_slug=company_slug)


@login_required
@company_access_required(require_admin=False, allow_user_role=False)
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
        # Usuários padrão vão para o verificador
        return redirect(f'/{user.company.slug}/verificador/')

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
        form = CustomUserForm(request.POST, current_user=request.user)
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
        form = CustomUserForm(current_user=request.user)
    return render(request, 'company/users/form.html', {'form': form, 'company': company})


@login_required
@company_access_required(require_admin=True)
def company_user_edit(request, company_slug, user_id):
    company = get_object_or_404(Company, slug=company_slug)
    user_obj = get_object_or_404(CustomUser, id=user_id, company=company)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_obj, current_user=request.user)
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
        form = CustomUserChangeForm(instance=user_obj, current_user=request.user)
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
    """
    Exclui uma empresa com validações de segurança e dependências
    
    Validações:
    - Verifica se empresa existe
    - Conta dependências (usuários, mapas)
    - Requer confirmação explícita
    - Faz backup/log da ação
    - Remove em transação para garantir integridade
    """
    company = get_object_or_404(Company, id=company_id)
    
    # Verificar confirmação
    confirmed = request.POST.get('confirmed', 'false').lower() == 'true'
    if not confirmed:
        # Retornar informações sobre dependências para confirmação
        user_count = company.users.count()
        map_count = company.cto_maps.count()
        
        return JsonResponse({
            'success': False,
            'requires_confirmation': True,
            'message': 'Confirmação necessária para excluir empresa',
            'dependencies': {
                'users': user_count,
                'maps': map_count,
                'company_name': company.name
            },
            'warning': f'A exclusão desta empresa também excluirá {user_count} usuário(s) e {map_count} mapa(s) associado(s).'
        }, status=400)
    
    # Validar dependências
    user_count = company.users.count()
    map_count = company.cto_maps.count()
    
    # Log da tentativa de exclusão
    logger.warning(
        f"Tentativa de exclusão de empresa: {company.name} (ID: {company.id})",
        extra={
            'user_id': request.user.id,
            'company_id': company.id,
            'company_name': company.name,
            'user_count': user_count,
            'map_count': map_count,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # Executar exclusão em transação
    try:
        with transaction.atomic():
            # Coletar informações antes da exclusão para log
            company_info = {
                'name': company.name,
                'cnpj': company.cnpj,
                'email': company.email,
                'slug': company.slug,
                'user_count': user_count,
                'map_count': map_count
            }
            
            # Remover arquivos físicos dos mapas antes de excluir
            for map_file in company.cto_maps.all():
                try:
                    if map_file.file and os.path.exists(map_file.file.path):
                        os.remove(map_file.file.path)
                        logger.debug(f"Arquivo de mapa removido: {map_file.file.path}")
                except Exception as file_error:
                    logger.warning(f"Erro ao remover arquivo de mapa {map_file.id}: {file_error}")
            
            # Excluir empresa (cascata excluirá usuários e mapas do banco)
            company.delete()
            
            # Log da exclusão bem-sucedida
            logger.info(
                f"Empresa excluída com sucesso: {company_info['name']}",
                extra={
                    'user_id': request.user.id,
                    'deleted_company': company_info,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Registrar no audit log
            try:
                from .audit_logger import log_user_action
                log_user_action(
                    user=request.user,
                    action='company_deleted',
                    details={
                        'company_name': company_info['name'],
                        'company_cnpj': company_info['cnpj'],
                        'users_deleted': user_count,
                        'maps_deleted': map_count
                    }
                )
            except Exception as audit_error:
                logger.warning(f"Erro ao registrar no audit log: {audit_error}")
            
            return JsonResponse({
                'success': True,
                'message': f'Empresa "{company_info["name"]}" excluída com sucesso',
                'deleted': {
                    'company': company_info['name'],
                    'users': user_count,
                    'maps': map_count
                }
            })
            
    except Exception as e:
        logger.error(
            f"Erro ao excluir empresa {company.id}: {str(e)}",
            extra={
                'user_id': request.user.id,
                'company_id': company.id,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            },
            exc_info=True
        )
        
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir empresa: {str(e)}'
        }, status=500)


# === RELATÓRIOS E EXPORTAÇÃO ===

@login_required
@rm_admin_required
def rm_reports_dashboard(request):
    """Dashboard de relatórios para RM"""
    metrics = ReportGenerator.get_system_wide_metrics()
    
    context = {
        'metrics': metrics,
        'title': 'Relatórios do Sistema'
    }
    return render(request, 'rm/reports/dashboard.html', context)

@login_required
@company_access_required
def company_reports_dashboard(request, company_slug):
    """Dashboard de relatórios da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    metrics = ReportGenerator.get_company_metrics(company)
    
    context = {
        'company': company,
        'metrics': metrics,
        'title': 'Relatórios da Empresa'
    }
    return render(request, 'company/reports/dashboard.html', context)

@login_required
@rm_admin_required
def export_system_report(request, format='csv'):
    """Exportar relatório do sistema"""
    metrics = ReportGenerator.get_system_wide_metrics()
    
    # Preparar dados para exportação
    export_data = []
    
    # Dados de empresas
    for company_data in metrics['company_rankings']:
        export_data.append({
            'Tipo': 'Empresa',
            'Nome': company_data.name,
            'Usuários': company_data.user_count,
            'Mapas': company_data.map_count,
            'Criada em': company_data.created_at
        })
    
    # Dados de uso
    for usage_data in metrics['usage_statistics']['maps_by_company']:
        export_data.append({
            'Tipo': 'Uso de Mapas',
            'Empresa': usage_data.name,
            'Total de Mapas': usage_data.map_count,
            'Data': timezone.now().strftime('%Y-%m-%d')
        })
    
    filename = f'relatorio_sistema_{timezone.now().strftime("%Y%m%d")}.{format}'
    
    if format == 'csv':
        return ExportManager.export_to_csv(export_data, filename)
    else:
        return ExportManager.export_to_json(export_data, filename)

@login_required
@company_access_required
def export_company_report(request, company_slug, format='csv'):
    """Exportar relatório da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    metrics = ReportGenerator.get_company_metrics(company)
    
    # Preparar dados para exportação
    export_data = []
    
    # Informações da empresa
    export_data.append({
        'Tipo': 'Informações da Empresa',
        'Nome': company.name,
        'Email': company.email,
        'Telefone': company.phone,
        'Total de Usuários': metrics['company_info']['total_users'],
        'Usuários Ativos': metrics['company_info']['active_users'],
        'Total de Mapas': metrics['map_statistics']['total_maps']
    })
    
    # Estatísticas de mapas
    for file_type in metrics['map_statistics']['by_file_type']:
        export_data.append({
            'Tipo': 'Estatísticas de Mapas',
            'Tipo de Arquivo': file_type['file_type'],
            'Quantidade': file_type['count'],
            'Empresa': company.name
        })
    
    filename = f'relatorio_{company.slug}_{timezone.now().strftime("%Y%m%d")}.{format}'
    
    if format == 'csv':
        return ExportManager.export_to_csv(export_data, filename)
    else:
        return ExportManager.export_to_json(export_data, filename)

@login_required
@company_access_required
def export_user_list(request, company_slug, format='csv'):
    """Exportar lista de usuários da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    users = CustomUser.objects.filter(company=company)
    
    export_data = []
    for user in users:
        export_data.append({
            'Username': user.username,
            'Email': user.email,
            'Nome Completo': f"{user.first_name} {user.last_name}".strip(),
            'Telefone': user.phone or '',
            'Role': user.get_role_display(),
            'Ativo': 'Sim' if user.is_active else 'Não',
            'Último Login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Nunca',
            'Data de Criação': user.date_joined.strftime('%Y-%m-%d %H:%M')
        })
    
    filename = f'usuarios_{company.slug}_{timezone.now().strftime("%Y%m%d")}.{format}'
    
    if format == 'csv':
        return ExportManager.export_to_csv(export_data, filename)
    else:
        return ExportManager.export_to_json(export_data, filename)

@login_required
@company_access_required
def export_map_list(request, company_slug, format='csv'):
    """Exportar lista de mapas da empresa"""
    company = get_object_or_404(Company, slug=company_slug)
    maps = CTOMapFile.objects.filter(company=company)
    
    export_data = []
    for map_file in maps:
        export_data.append({
            'Nome do Arquivo': map_file.original_filename,
            'Tipo': map_file.file_type,
            'Tamanho (MB)': round(map_file.file_size / (1024 * 1024), 2) if map_file.file_size else 0,
            'Status': map_file.status,
            'Uploadado por': map_file.uploaded_by.get_full_name() if map_file.uploaded_by else 'Sistema',
            'Data de Upload': map_file.uploaded_at.strftime('%Y-%m-%d %H:%M')
        })
    
    filename = f'mapas_{company.slug}_{timezone.now().strftime("%Y%m%d")}.{format}'
    
    if format == 'csv':
        return ExportManager.export_to_csv(export_data, filename)
    else:
        return ExportManager.export_to_json(export_data, filename)
