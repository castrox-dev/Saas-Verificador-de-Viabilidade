#!/usr/bin/env python
"""
Script para testar se os arquivos estáticos estão sendo servidos corretamente
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse

def test_static_files():
    """Testa se os arquivos estáticos estão acessíveis"""
    client = Client()
    
    # Lista de arquivos estáticos para testar
    static_files = [
        '/static/css/login.css',
        '/static/js/login.js',
        '/static/js/dark-mode.js',
        '/static/img/logo_letreiro.png',
        '/static/css/theme_rm.css',
        '/static/css/global.css',
    ]
    
    print("🔍 Testando arquivos estáticos...")
    print("=" * 50)
    
    for file_path in static_files:
        try:
            response = client.get(file_path)
            if response.status_code == 200:
                content_type = response.get('Content-Type', '')
                print(f"✅ {file_path} - Status: {response.status_code} - Type: {content_type}")
            else:
                print(f"❌ {file_path} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Erro: {e}")
    
    print("\n" + "=" * 50)
    print("📁 Verificando diretórios...")
    
    # Verificar se os diretórios existem
    static_dirs = [
        settings.STATICFILES_DIRS[0],
        settings.STATIC_ROOT,
    ]
    
    for static_dir in static_dirs:
        if static_dir.exists():
            print(f"✅ {static_dir} existe")
        else:
            print(f"❌ {static_dir} não existe")
    
    print("\n📊 Configurações:")
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"DEBUG: {settings.DEBUG}")

if __name__ == "__main__":
    test_static_files()
