from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import json
import os
import tempfile

from core.models import Company
from .models import GeocodingCache, ViabilidadeCache, CTOFile
from .services import VerificadorService
from .geocoding import GeocodingService
from .utils import get_all_ctos, classificar_viabilidade

User = get_user_model()


class VerificadorIntegrationTests(TestCase):
    """Testes de integração do verificador"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        # Criar empresa de teste
        self.company = Company.objects.create(
            name="Empresa Teste",
            slug="empresa-teste",
            cnpj="12345678000199",
            email="teste@empresa.com"
        )
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            company=self.company,
            role="COMPANY_ADMIN"
        )
        
        # Cliente de teste
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_geocoding_cache(self):
        """Testa o sistema de cache de geocodificação"""
        # Testar geocodificação
        endereco = "Rua das Flores, 123, Rio de Janeiro"
        resultado = GeocodingService.geocodificar(endereco)
        
        if resultado:  # Se a geocodificação funcionou
            # Verificar se foi salvo no cache
            cache_obj = GeocodingCache.objects.get(endereco=endereco)
            self.assertEqual(cache_obj.lat, resultado['lat'])
            self.assertEqual(cache_obj.lng, resultado['lng'])
            
            # Testar cache hit
            resultado_cached = GeocodingService.geocodificar(endereco)
            self.assertEqual(resultado, resultado_cached)
    
    def test_viability_classification(self):
        """Testa a classificação de viabilidade"""
        # Testar diferentes distâncias
        casos = [
            (200, "Viável"),
            (500, "Viabilidade Limitada"),
            (1200, "Sem viabilidade")
        ]
        
        for distancia, status_esperado in casos:
            resultado = classificar_viabilidade(distancia)
            self.assertEqual(resultado['status'], status_esperado)
    
    def test_api_arquivos_ftth(self):
        """Testa a API de arquivos FTTH"""
        response = self.client.get('/verificador/api/arquivos/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
    
    def test_api_geocode(self):
        """Testa a API de geocodificação"""
        response = self.client.get('/verificador/api/geocode/', {
            'endereco': 'Rua das Flores, 123, Rio de Janeiro'
        })
        
        # Pode retornar 200 (encontrado) ou 404 (não encontrado)
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            data = json.loads(response.content)
            self.assertIn('lat', data)
            self.assertIn('lng', data)
    
    def test_verificador_view_access(self):
        """Testa acesso às views do verificador"""
        # Testar view simples
        response = self.client.get(f'/verificador/{self.company.slug}/')
        self.assertEqual(response.status_code, 200)
        
        # Testar view completa
        response = self.client.get(f'/verificador/{self.company.slug}/mapa/')
        self.assertEqual(response.status_code, 200)
    
    def test_verificador_apis_authenticated(self):
        """Testa APIs autenticadas do verificador"""
        # Testar listagem de arquivos da empresa
        response = self.client.get(f'/verificador/{self.company.slug}/api/arquivos/')
        self.assertEqual(response.status_code, 200)
        
        # Testar verificação de viabilidade
        response = self.client.get(f'/verificador/{self.company.slug}/api/verificar-viabilidade/', {
            'lat': '-22.9068',
            'lon': '-43.1729'
        })
        # Pode retornar 200 (sucesso) ou 404 (nenhum CTO)
        self.assertIn(response.status_code, [200, 404])
    
    def test_verificador_service_integration(self):
        """Testa integração do serviço de verificação"""
        # Testar verificação de arquivo
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=True) as tmp_file:
            # Criar arquivo CSV de teste
            csv_content = "nome,lat,lng\nCTO Teste,-22.9068,-43.1729"
            tmp_file.write(csv_content.encode())
            tmp_file.flush()
            
            resultado = VerificadorService.verificar_arquivo(tmp_file.name, 'csv')
            self.assertTrue(resultado.get('success', False))
    
    def test_cache_management_apis(self):
        """Testa APIs de gerenciamento de cache"""
        # Testar estatísticas do cache
        response = self.client.get('/verificador/api/cache/geocoding/stats/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('total_entries', data)
        self.assertIn('valid_entries', data)
        
        # Testar limpeza do cache
        response = self.client.post('/verificador/api/cache/geocoding/clear/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_check(self):
        """Testa health check do verificador"""
        # Health check pode redirecionar para login em alguns casos
        client_anonimo = Client()
        response = client_anonimo.get('/verificador/health/')
        
        # Pode retornar 200 (sucesso) ou 302 (redirecionamento para login)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'online')
            self.assertEqual(data['service'], 'Django Verificador')


class VerificadorPerformanceTests(TestCase):
    """Testes de performance do verificador"""
    
    def setUp(self):
        """Configuração para testes de performance"""
        self.company = Company.objects.create(
            name="Empresa Performance",
            slug="empresa-performance",
            cnpj="98765432000199",
            email="perf@empresa.com"
        )
        
        self.user = User.objects.create_user(
            username="perfuser",
            email="perf@example.com",
            password="testpass123",
            company=self.company,
            role="COMPANY_ADMIN"
        )
        
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_viability_cache_performance(self):
        """Testa performance do cache de viabilidade"""
        import time
        
        # Primeira verificação (sem cache)
        start_time = time.time()
        response = self.client.get(f'/verificador/{self.company.slug}/api/verificar-viabilidade/', {
            'lat': '-22.9068',
            'lon': '-43.1729'
        })
        first_time = time.time() - start_time
        
        # Segunda verificação (com cache)
        start_time = time.time()
        response = self.client.get(f'/verificador/{self.company.slug}/api/verificar-viabilidade/', {
            'lat': '-22.9068',
            'lon': '-43.1729'
        })
        second_time = time.time() - start_time
        
        # A segunda verificação deve ser mais rápida (cache hit)
        if response.status_code == 200:
            self.assertLess(second_time, first_time)
