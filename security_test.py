#!/usr/bin/env python3
"""
Script de teste de segurança para rmsys.com.br
Execute com: python security_test.py
"""

import os
import sys
import django
import time
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class SecurityTester:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.client = Client()
        self.results = []
    
    def log_test(self, test_name, status, details=''):
        """Registrar resultado do teste"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def test_1_authentication_required(self):
        """Teste 1: Verificar se autenticação é obrigatória"""
        try:
            # Tentar acessar área administrativa sem login
            response = self.client.get('/rm/admin/')
            if response.status_code == 302:  # Redirect para login
                self.log_test("Autenticação obrigatória", "PASS", "Redirect para login")
            else:
                self.log_test("Autenticação obrigatória", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Autenticação obrigatória", "ERROR", str(e))
    
    def test_2_company_isolation(self):
        """Teste 2: Verificar isolamento entre empresas"""
        try:
            # Criar usuários de empresas diferentes
            company1_user = User.objects.create_user(
                username='test_company1',
                email='test1@company1.com',
                password='testpass123',
                role='COMPANY_USER',
                company_id=1  # Assumindo empresa ID 1
            )
            
            company2_user = User.objects.create_user(
                username='test_company2',
                email='test2@company2.com',
                password='testpass123',
                role='COMPANY_USER',
                company_id=2  # Assumindo empresa ID 2
            )
            
            # Login como usuário da empresa 1
            self.client.force_login(company1_user)
            
            # Tentar acessar dados da empresa 2
            response = self.client.get('/company2/dashboard/')
            if response.status_code == 403:
                self.log_test("Isolamento entre empresas", "PASS", "Acesso negado corretamente")
            else:
                self.log_test("Isolamento entre empresas", "FAIL", f"Status: {response.status_code}")
            
            # Cleanup
            company1_user.delete()
            company2_user.delete()
            
        except Exception as e:
            self.log_test("Isolamento entre empresas", "ERROR", str(e))
    
    def test_3_rate_limiting(self):
        """Teste 3: Verificar rate limiting"""
        try:
            # Múltiplas tentativas de login
            for i in range(10):
                response = self.client.post('/rm/login/', {
                    'username': 'admin',
                    'password': 'wrong_password'
                })
                time.sleep(0.1)  # Pequena pausa entre tentativas
            
            # Verificar se rate limiting foi ativado
            response = self.client.post('/rm/login/', {
                'username': 'admin',
                'password': 'wrong_password'
            })
            
            if response.status_code == 429:  # Too Many Requests
                self.log_test("Rate limiting", "PASS", "Bloqueio após muitas tentativas")
            else:
                self.log_test("Rate limiting", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Rate limiting", "ERROR", str(e))
    
    def test_4_file_validation(self):
        """Teste 4: Verificar validação de arquivos"""
        try:
            # Teste 1: Arquivo malicioso
            malicious_content = b'MZ\x90\x00'  # Header de executável
            malicious_file = {
                'file': ('malicious.exe', malicious_content, 'application/octet-stream')
            }
            
            response = self.client.post('/rm/mapas/upload/', {
                'file': malicious_file,
                'description': 'Teste de segurança'
            })
            
            if response.status_code == 400:  # Bad Request
                self.log_test("Validação de arquivos (malicioso)", "PASS", "Arquivo malicioso rejeitado")
            else:
                self.log_test("Validação de arquivos (malicioso)", "FAIL", f"Status: {response.status_code}")
            
            # Teste 2: Arquivo KML válido
            kml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Teste CTO</name>
      <Point>
        <coordinates>-46.6333,-23.5505,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>'''
            
            kml_file = {
                'file': ('teste_cto.kml', kml_content, 'application/vnd.google-earth.kml+xml')
            }
            
            response = self.client.post('/rm/mapas/upload/', {
                'file': kml_file,
                'description': 'Teste KML válido'
            })
            
            if response.status_code in [200, 302]:  # Sucesso ou redirect
                self.log_test("Validação de arquivos (KML)", "PASS", "Arquivo KML aceito")
            else:
                self.log_test("Validação de arquivos (KML)", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Validação de arquivos", "ERROR", str(e))
    
    def test_5_security_headers(self):
        """Teste 5: Verificar headers de segurança"""
        try:
            response = self.client.get('/')
            headers = response.headers
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            }
            
            missing_headers = []
            for header, expected_value in security_headers.items():
                if header not in headers or headers[header] != expected_value:
                    missing_headers.append(f"{header}: {headers.get(header, 'MISSING')}")
            
            if not missing_headers:
                self.log_test("Headers de segurança", "PASS", "Todos os headers presentes")
            else:
                self.log_test("Headers de segurança", "FAIL", f"Headers faltando: {', '.join(missing_headers)}")
                
        except Exception as e:
            self.log_test("Headers de segurança", "ERROR", str(e))
    
    def test_6_password_validation(self):
        """Teste 6: Verificar validação de senhas"""
        try:
            # Tentar criar usuário com senha fraca
            weak_passwords = [
                '123456',
                'password',
                'admin',
                'test'
            ]
            
            for weak_pass in weak_passwords:
                try:
                    user = User.objects.create_user(
                        username=f'test_weak_{weak_pass}',
                        email=f'test_{weak_pass}@test.com',
                        password=weak_pass
                    )
                    # Se chegou aqui, a senha foi aceita (problema)
                    user.delete()
                    self.log_test("Validação de senhas", "FAIL", f"Senha fraca aceita: {weak_pass}")
                    return
                except Exception:
                    # Senha rejeitada (bom)
                    continue
            
            self.log_test("Validação de senhas", "PASS", "Senhas fracas rejeitadas")
            
        except Exception as e:
            self.log_test("Validação de senhas", "ERROR", str(e))
    
    def test_7_csrf_protection(self):
        """Teste 7: Verificar proteção CSRF"""
        try:
            # Tentar POST sem CSRF token
            response = self.client.post('/rm/login/', {
                'username': 'admin',
                'password': 'test'
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            if response.status_code == 403:  # Forbidden (CSRF)
                self.log_test("Proteção CSRF", "PASS", "CSRF token obrigatório")
            else:
                self.log_test("Proteção CSRF", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Proteção CSRF", "ERROR", str(e))
    
    def test_8_session_security(self):
        """Teste 8: Verificar segurança de sessão"""
        try:
            # Verificar configurações de sessão
            session_settings = {
                'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
                'SESSION_COOKIE_HTTPONLY': getattr(settings, 'SESSION_COOKIE_HTTPONLY', False),
                'SESSION_COOKIE_SAMESITE': getattr(settings, 'SESSION_COOKIE_SAMESITE', None),
                'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
            }
            
            secure_settings = all([
                session_settings['SESSION_COOKIE_SECURE'],
                session_settings['SESSION_COOKIE_HTTPONLY'],
                session_settings['SESSION_COOKIE_SAMESITE'] == 'Strict',
                session_settings['CSRF_COOKIE_SECURE']
            ])
            
            if secure_settings:
                self.log_test("Segurança de sessão", "PASS", "Configurações seguras")
            else:
                self.log_test("Segurança de sessão", "FAIL", f"Configurações: {session_settings}")
                
        except Exception as e:
            self.log_test("Segurança de sessão", "ERROR", str(e))
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🔒 Iniciando testes de segurança...")
        print("=" * 50)
        
        self.test_1_authentication_required()
        self.test_2_company_isolation()
        self.test_3_rate_limiting()
        self.test_4_file_validation()
        self.test_5_security_headers()
        self.test_6_password_validation()
        self.test_7_csrf_protection()
        self.test_8_session_security()
        
        # Resumo
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS TESTES")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        total = len(self.results)
        
        print(f"✅ Passou: {passed}/{total}")
        print(f"❌ Falhou: {failed}/{total}")
        print(f"⚠️ Erro: {errors}/{total}")
        
        if failed == 0 and errors == 0:
            print("\n🎉 TODOS OS TESTES DE SEGURANÇA PASSARAM!")
            print("✅ Sistema seguro para produção!")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM!")
            print("❌ Corrija os problemas antes do deploy!")
        
        return self.results

def main():
    """Função principal"""
    tester = SecurityTester()
    results = tester.run_all_tests()
    
    # Salvar resultados em arquivo
    with open('security_test_results.json', 'w') as f:
        import json
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Resultados salvos em: security_test_results.json")

if __name__ == '__main__':
    main()
