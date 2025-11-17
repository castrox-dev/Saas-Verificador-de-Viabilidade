"""
Utilitários para o sistema
"""
import secrets
import string
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site


def generate_random_password(length=12, simple=False):
    """
    Gera uma senha aleatória
    
    Args:
        length (int): Tamanho da senha (padrão: 12)
        simple (bool): Se True, gera senha simples com letras e números (sem símbolos)
    
    Returns:
        str: Senha aleatória
    """
    if simple:
        # Senha simples com letras (maiúsculas e minúsculas) e números
        # Garantir que tenha pelo menos uma letra minúscula, uma maiúscula e um número
        password = [
            secrets.choice(string.ascii_lowercase),  # Pelo menos 1 letra minúscula
            secrets.choice(string.ascii_uppercase),  # Pelo menos 1 letra maiúscula
            secrets.choice(string.digits),           # Pelo menos 1 número
        ]
        
        # Preencher o resto com letras e números aleatórios
        alphabet = string.ascii_letters + string.digits
        for _ in range(length - 3):
            password.append(secrets.choice(alphabet))
        
        # Embaralhar a senha
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    # Caracteres permitidos: letras minúsculas, maiúsculas, números e símbolos
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    
    # Garantir que a senha tenha pelo menos:
    # - 1 letra minúscula
    # - 1 letra maiúscula
    # - 1 número
    # - 1 símbolo
    
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*")
    ]
    
    # Preencher o resto com caracteres aleatórios
    for _ in range(length - 4):
        password.append(secrets.choice(alphabet))
    
    # Embaralhar a senha
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def send_user_credentials_email(user, plain_password, request=None):
    """
    Envia email com credenciais do novo usuário
    
    Args:
        user: Instância do CustomUser
        plain_password: Senha em texto plano (para enviar no email)
        request: Objeto HttpRequest (para obter domain)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Obter informações do site
        if request:
            current_site = get_current_site(request)
            domain = current_site.domain
            protocol = 'https' if request.is_secure() else 'http'
        else:
            domain = getattr(settings, 'SITE_DOMAIN', 'verificador.up.railway.app')
            protocol = 'https'
        
        # Determinar URL de login baseado no role
        if user.role == 'RM' or not user.company:
            login_url = f"{protocol}://{domain}/rm/login/"
            user_type = "RM Systems"
        else:
            login_url = f"{protocol}://{domain}/{user.company.slug}/login/"
            user_type = user.company.name
        
        # Contexto para o template
        context = {
            'user': user,
            'password': plain_password,
            'login_url': login_url,
            'user_type': user_type,
            'domain': domain,
            'protocol': protocol,
        }
        
        # Renderizar email
        subject = render_to_string(
            'core/email/user_credentials_subject.txt',
            context
        ).strip()
        
        message = render_to_string(
            'core/email/user_credentials_email.html',
            context
        )
        
        # Enviar email
        send_mail(
            subject=subject,
            message='',  # Mensagem vazia porque usamos HTML
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao enviar email com credenciais para {user.email}: {str(e)}", exc_info=True)
        return False


def send_ticket_created_email(ticket, request=None):
    """
    Envia email quando um ticket é criado
    
    Args:
        ticket: Instância do Ticket
        request: Objeto HttpRequest (para obter domain)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Obter informações do site
        if request:
            current_site = get_current_site(request)
            domain = current_site.domain
            protocol = 'https' if request.is_secure() else 'http'
        else:
            domain = getattr(settings, 'SITE_DOMAIN', 'verificador.up.railway.app')
            protocol = 'https'
        
        # URL de visualização do ticket
        if ticket.company:
            ticket_url = f"{protocol}://{domain}/{ticket.company.slug}/tickets/{ticket.id}/"
        else:
            ticket_url = f"{protocol}://{domain}/rm/tickets/{ticket.id}/"
        
        # Contexto para o template
        context = {
            'ticket': ticket,
            'user': ticket.created_by,
            'company': ticket.company,
            'ticket_url': ticket_url,
            'domain': domain,
            'protocol': protocol,
        }
        
        # Renderizar email
        subject = render_to_string(
            'core/email/ticket_created_subject.txt',
            context
        ).strip()
        
        message = render_to_string(
            'core/email/ticket_created_email.html',
            context
        )
        
        # Enviar email para o criador do ticket
        send_mail(
            subject=subject,
            message='',
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.created_by.email],
            fail_silently=False,
        )
        
        # Enviar também para RM admins (opcional - pode ser configurado)
        if ticket.company:
            # Enviar para email da empresa também
            if ticket.company.email:
                send_mail(
                    subject=f"[Ticket {ticket.ticket_number}] {subject}",
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.company.email],
                    fail_silently=False,
                )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao enviar email de ticket criado: {str(e)}", exc_info=True)
        return False


def send_ticket_message_email(ticket, message, request=None):
    """
    Envia email quando uma nova mensagem é adicionada ao ticket
    
    Args:
        ticket: Instância do Ticket
        message: Instância do TicketMessage
        request: Objeto HttpRequest
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        if request:
            current_site = get_current_site(request)
            domain = current_site.domain
            protocol = 'https' if request.is_secure() else 'http'
        else:
            domain = getattr(settings, 'SITE_DOMAIN', 'verificador.up.railway.app')
            protocol = 'https'
        
        # URL de visualização do ticket
        if ticket.company:
            ticket_url = f"{protocol}://{domain}/{ticket.company.slug}/tickets/{ticket.id}/"
        else:
            ticket_url = f"{protocol}://{domain}/rm/tickets/{ticket.id}/"
        
        # Determinar destinatário
        if message.sent_by == ticket.created_by:
            # Mensagem do cliente, enviar para RM
            # Enviar para todos os RM admins se não houver atendente atribuído
            if not ticket.assigned_to:
                from .models import CustomUser
                rm_admins = CustomUser.objects.filter(role='RM', is_active=True)
                recipients = [admin.email for admin in rm_admins if admin.email and admin.email]
                if not recipients:
                    recipients = [settings.DEFAULT_FROM_EMAIL]
            else:
                recipients = [ticket.assigned_to.email] if ticket.assigned_to.email else [settings.DEFAULT_FROM_EMAIL]
        else:
            # Mensagem do RM, enviar para o cliente
            recipients = [ticket.created_by.email] if ticket.created_by.email else [settings.DEFAULT_FROM_EMAIL]
        
        context = {
            'ticket': ticket,
            'message': message,
            'sender': message.sent_by,
            'ticket_url': ticket_url,
            'domain': domain,
            'protocol': protocol,
        }
        
        subject = render_to_string(
            'core/email/ticket_message_subject.txt',
            context
        ).strip()
        
        message_html = render_to_string(
            'core/email/ticket_message_email.html',
            context
        )
        
        for recipient_email in recipients:
            send_mail(
                subject=subject,
                message='',
                html_message=message_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao enviar email de nova mensagem: {str(e)}", exc_info=True)
        return False

