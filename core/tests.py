"""
Testes automatizados para RM Systems SaaS
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
import json

from .models import Company, CTOMapFile
from .forms import CustomUserForm, CustomUserChangeForm

User = get_user_model()

class CompanyModelTest(TestCase):
    """Testes para o modelo Company"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com",
            phone="123456789"
        )
    
    def test_company_creation(self):
        """Teste de criação de empresa"""
        self.assertEqual(self.company.name, "Test Company")
        self.assertEqual(self.company.slug, "test-company")
        self.assertTrue(self.company.created_at)
    
    def test_company_str(self):
        """Teste do método __str__"""
        self.assertEqual(str(self.company), "Test Company")

class UserModelTest(TestCase):
    """Testes para o modelo User"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="company_admin"
        )
    
    def test_user_creation(self):
        """Teste de criação de usuário"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.company, self.company)
        self.assertEqual(self.user.role, "company_admin")
    
    def test_user_str(self):
        """Teste do método __str__"""
        self.assertEqual(str(self.user), "testuser")

class LoginViewTest(TestCase):
    """Testes para views de login"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company
        )
    
    def test_login_success(self):
        """Teste de login bem-sucedido"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect após login
    
    def test_login_failure(self):
        """Teste de login com credenciais inválidas"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Página de login
        self.assertContains(response, "Credenciais inválidas")
    
    def test_company_login_success(self):
        """Teste de login de empresa"""
        response = self.client.post(f'/company/{self.company.slug}/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

class DashboardViewTest(TestCase):
    """Testes para views de dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="company_admin"
        )
        self.client.login(username="testuser", password="testpass123")
    
    def test_company_dashboard_access(self):
        """Teste de acesso ao dashboard da empresa"""
        response = self.client.get(f'/company/{self.company.slug}/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Company")
    
    def test_rm_dashboard_access_denied(self):
        """Teste de acesso negado ao dashboard RM"""
        response = self.client.get('/rm/dashboard/')
        self.assertEqual(response.status_code, 403)

class UserManagementTest(TestCase):
    """Testes para gerenciamento de usuários"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@company.com",
            password="adminpass123",
            company=self.company,
            role="company_admin"
        )
        self.client.login(username="admin", password="adminpass123")
    
    def test_user_creation_form(self):
        """Teste do formulário de criação de usuário"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@company.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'role': 'company_user',
            'company': self.company.id
        }
        form = CustomUserForm(data=form_data, current_user=self.admin)
        self.assertTrue(form.is_valid())
    
    def test_user_creation_view(self):
        """Teste da view de criação de usuário"""
        response = self.client.post(f'/company/{self.company.slug}/painel/usuarios/novo/', {
            'username': 'newuser',
            'email': 'newuser@company.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'role': 'company_user',
            'company': self.company.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect após criação
        self.assertTrue(User.objects.filter(username='newuser').exists())

class FileUploadTest(TestCase):
    """Testes para upload de arquivos"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="company_admin"
        )
        self.client.login(username="testuser", password="testpass123")
    
    def test_file_upload_success(self):
        """Teste de upload bem-sucedido"""
        # Criar arquivo CSV de teste
        csv_content = "name,value\nTest,123"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post(f'/company/{self.company.slug}/verificador/', {
            'file': csv_file,
            'description': 'Test file'
        })
        
        # Verificar se o arquivo foi criado
        self.assertTrue(CTOMapFile.objects.filter(original_filename='test.csv').exists())
    
    def test_file_upload_invalid_type(self):
        """Teste de upload com tipo inválido"""
        # Criar arquivo de texto simples
        txt_content = "This is a text file"
        txt_file = SimpleUploadedFile(
            "test.txt",
            txt_content.encode(),
            content_type="text/plain"
        )
        
        response = self.client.post(f'/company/{self.company.slug}/verificador/', {
            'file': txt_file,
            'description': 'Test file'
        })
        
        # Verificar se o arquivo NÃO foi criado
        self.assertFalse(CTOMapFile.objects.filter(original_filename='test.txt').exists())

class APITest(TestCase):
    """Testes para API REST"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="rm_admin"
        )
        self.client.login(username="testuser", password="testpass123")
    
    def test_api_companies_list(self):
        """Teste da API de listagem de empresas"""
        response = self.client.get('/api/companies/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "Test Company")
    
    def test_api_company_stats(self):
        """Teste da API de estatísticas da empresa"""
        response = self.client.get(f'/api/companies/{self.company.id}/stats/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total_users', data)
        self.assertIn('total_maps', data)

class SecurityTest(TestCase):
    """Testes de segurança"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="company_user"
        )
    
    def test_unauthorized_access(self):
        """Teste de acesso não autorizado"""
        # Tentar acessar dashboard sem login
        response = self.client.get(f'/company/{self.company.slug}/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect para login
    
    def test_cross_company_access(self):
        """Teste de acesso entre empresas"""
        # Criar outra empresa
        other_company = Company.objects.create(
            name="Other Company",
            email="other@company.com"
        )
        
        self.client.login(username="testuser", password="testpass123")
        
        # Tentar acessar dashboard de outra empresa
        response = self.client.get(f'/company/{other_company.slug}/dashboard/')
        self.assertEqual(response.status_code, 403)  # Acesso negado

class PerformanceTest(TestCase):
    """Testes de performance"""
    
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(
            name="Test Company",
            email="test@company.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.com",
            password="testpass123",
            company=self.company,
            role="company_admin"
        )
        self.client.login(username="testuser", password="testpass123")
    
    def test_dashboard_performance(self):
        """Teste de performance do dashboard"""
        import time
        
        start_time = time.time()
        response = self.client.get(f'/company/{self.company.slug}/dashboard/')
        end_time = time.time()
        
        # Verificar se a resposta foi rápida (menos de 1 segundo)
        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(response.status_code, 200)
    
    def test_large_dataset_performance(self):
        """Teste de performance com grande volume de dados"""
        # Criar muitos usuários
        for i in range(100):
            User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@company.com",
                password="testpass123",
                company=self.company,
                role="company_user"
            )
        
        # Testar performance da listagem
        import time
        start_time = time.time()
        response = self.client.get(f'/company/{self.company.slug}/painel/usuarios/')
        end_time = time.time()
        
        # Verificar se a resposta foi rápida mesmo com muitos dados
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(response.status_code, 200)