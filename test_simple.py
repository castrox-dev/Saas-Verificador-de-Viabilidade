#!/usr/bin/env python3
"""
Teste simples de segurança para desenvolvimento
Execute com: python test_simple.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def test_basic_security():
    """Teste básico de segurança"""
    print("🔒 Testando segurança básica...")
    
    client = Client()
    
    # Teste 1: Acesso sem autenticação
    print("1. Testando acesso sem autenticação...")
    response = client.get('/rm/admin/')
    if response.status_code == 302:
        print("   ✅ Redirect para login funcionando")
    else:
        print(f"   ❌ Status inesperado: {response.status_code}")
    
    # Teste 2: Headers de segurança
    print("2. Testando headers de segurança...")
    response = client.get('/')
    headers = response.headers
    
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
    }
    
    missing = []
    for header, expected in security_headers.items():
        if header not in headers:
            missing.append(header)
    
    if not missing:
        print("   ✅ Headers de segurança presentes")
    else:
        print(f"   ⚠️ Headers faltando: {', '.join(missing)}")
    
    # Teste 3: Configurações de sessão
    print("3. Testando configurações de sessão...")
    session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
    session_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', False)
    
    if session_httponly:
        print("   ✅ SESSION_COOKIE_HTTPONLY habilitado")
    else:
        print("   ⚠️ SESSION_COOKIE_HTTPONLY desabilitado")
    
    if session_secure:
        print("   ✅ SESSION_COOKIE_SECURE habilitado")
    else:
        print("   ⚠️ SESSION_COOKIE_SECURE desabilitado (OK para desenvolvimento)")
    
    # Teste 4: Validação de senhas
    print("4. Testando validação de senhas...")
    try:
        user = User.objects.create_user(
            username='test_weak',
            email='test@test.com',
            password='123456'  # Senha fraca
        )
        print("   ❌ Senha fraca foi aceita!")
        user.delete()
    except Exception:
        print("   ✅ Senhas fracas são rejeitadas")
    
    print("\n🎯 Teste básico concluído!")

if __name__ == '__main__':
    test_basic_security()
