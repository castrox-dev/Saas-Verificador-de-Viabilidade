#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from core.models import Company, CustomUser

# Verificar empresa Fibramar
try:
    company = Company.objects.get(slug='fibramar')
    print(f"✅ Empresa encontrada: {company.name} - {company.slug}")
    print(f"   Ativa: {company.is_active}")
except Company.DoesNotExist:
    print("❌ Empresa 'fibramar' não encontrada!")
    print("Empresas disponíveis:")
    for c in Company.objects.all():
        print(f"  - {c.name} ({c.slug})")
    exit(1)

# Verificar usuários da Fibramar
users = CustomUser.objects.filter(company=company)
print(f"\n👥 Usuários da Fibramar: {users.count()}")

if users.count() == 0:
    print("❌ Nenhum usuário encontrado para a Fibramar!")
    print("Criando usuário de teste...")
    
    # Criar usuário de teste
    user = CustomUser.objects.create_user(
        username='teste_fibramar',
        email='teste@fibramar.com',
        password='123456',
        first_name='Teste',
        last_name='Fibramar',
        company=company,
        role='COMPANY_ADMIN',
        is_active=True
    )
    print(f"✅ Usuário criado: {user.username} ({user.role})")
else:
    for user in users:
        print(f"  - {user.username} ({user.role}) - Ativo: {user.is_active}")
        print(f"    Email: {user.email}")
        print(f"    Empresa: {user.company.name if user.company else 'Nenhuma'}")

print(f"\n🔍 Teste de autenticação:")
from django.contrib.auth import authenticate

# Testar autenticação
if users.count() > 0:
    test_user = users.first()
    auth_user = authenticate(username=test_user.username, password='123456')
    if auth_user:
        print(f"✅ Autenticação bem-sucedida: {auth_user.username}")
        print(f"   Empresa: {auth_user.company.name if auth_user.company else 'Nenhuma'}")
        print(f"   Slug da empresa: {auth_user.company.slug if auth_user.company else 'Nenhuma'}")
    else:
        print("❌ Falha na autenticação")
        print("Tentando com senha padrão...")
        auth_user = authenticate(username=test_user.username, password='admin123')
        if auth_user:
            print("✅ Autenticação com senha 'admin123' bem-sucedida")
        else:
            print("❌ Falha na autenticação com senha padrão")
