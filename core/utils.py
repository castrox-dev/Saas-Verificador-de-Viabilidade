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


def generate_random_password(length=12):
    """
    Gera uma senha aleatória segura
    
    Args:
        length (int): Tamanho da senha (padrão: 12)
    
    Returns:
        str: Senha aleatória
    """
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

