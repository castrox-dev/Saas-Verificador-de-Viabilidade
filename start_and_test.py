#!/usr/bin/env python
"""
Script para iniciar o Flask e testar a integração
"""
import subprocess
import time
import requests
import os
import sys

def start_flask():
    """Inicia o servidor Flask"""
    print("Iniciando servidor Flask...")
    
    # Mudar para o diretório do Flask
    flask_dir = "verificador_flask"
    if not os.path.exists(flask_dir):
        print("ERRO: Diretório verificador_flask não encontrado!")
        return False
    
    try:
        # Iniciar Flask em background
        process = subprocess.Popen(
            [sys.executable, "ftth_kml_app.py"],
            cwd=flask_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Flask iniciado em background...")
        
        # Aguardar Flask inicializar
        for i in range(10):
            try:
                response = requests.get("http://127.0.0.1:5000/health", timeout=2)
                if response.status_code == 200:
                    print("Flask está online!")
                    return True
            except:
                pass
            time.sleep(1)
            print(f"Aguardando Flask... ({i+1}/10)")
        
        print("ERRO: Flask não respondeu após 10 segundos")
        return False
        
    except Exception as e:
        print(f"ERRO ao iniciar Flask: {e}")
        return False

def test_flask_endpoints():
    """Testa os endpoints do Flask"""
    print("\nTestando endpoints do Flask:")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/api/arquivos", "Listar Arquivos"),
        ("/api/verificar-viabilidade?lat=-22.9068&lon=-43.1729", "Verificar Viabilidade")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:5000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   OK: {description}")
            else:
                print(f"   ERRO: {description} - Status {response.status_code}")
        except Exception as e:
            print(f"   ERRO: {description} - {e}")

def test_django_integration():
    """Testa a integração Django"""
    print("\nTestando integração Django:")
    
    try:
        # Executar teste de integração
        result = subprocess.run([
            sys.executable, "test_integration.py"
        ], capture_output=True, text=True, timeout=30)
        
        print("Resultado do teste:")
        print(result.stdout)
        
        if result.stderr:
            print("Erros:")
            print(result.stderr)
            
    except Exception as e:
        print(f"ERRO no teste Django: {e}")

if __name__ == "__main__":
    print("=== INICIANDO E TESTANDO INTEGRACAO ===")
    
    # 1. Iniciar Flask
    if start_flask():
        # 2. Testar endpoints Flask
        test_flask_endpoints()
        
        # 3. Testar integração Django
        test_django_integration()
        
        print("\n=== INTEGRACAO CONCLUIDA ===")
        print("Para manter Flask rodando, execute:")
        print("cd verificador_flask && python ftth_kml_app.py")
    else:
        print("ERRO: Não foi possível iniciar Flask")
