from django.core.management.base import BaseCommand
from core.models import Company, CustomUser
from django.contrib.auth import authenticate

class Command(BaseCommand):
    help = 'Debug login issues'

    def handle(self, *args, **options):
        # Verificar empresa Fibramar
        try:
            company = Company.objects.get(slug='fibramar')
            self.stdout.write(f"✅ Empresa encontrada: {company.name} - {company.slug}")
            self.stdout.write(f"   Ativa: {company.is_active}")
        except Company.DoesNotExist:
            self.stdout.write("❌ Empresa 'fibramar' não encontrada!")
            self.stdout.write("Empresas disponíveis:")
            for c in Company.objects.all():
                self.stdout.write(f"  - {c.name} ({c.slug})")
            return

        # Verificar usuários da Fibramar
        users = CustomUser.objects.filter(company=company)
        self.stdout.write(f"\n👥 Usuários da Fibramar: {users.count()}")

        if users.count() == 0:
            self.stdout.write("❌ Nenhum usuário encontrado para a Fibramar!")
            self.stdout.write("Criando usuário de teste...")
            
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
            self.stdout.write(f"✅ Usuário criado: {user.username} ({user.role})")
        else:
            for user in users:
                self.stdout.write(f"  - {user.username} ({user.role}) - Ativo: {user.is_active}")
                self.stdout.write(f"    Email: {user.email}")
                self.stdout.write(f"    Empresa: {user.company.name if user.company else 'Nenhuma'}")

        self.stdout.write(f"\n🔍 Teste de autenticação:")
        
        # Testar autenticação
        if users.count() > 0:
            test_user = users.first()
            auth_user = authenticate(username=test_user.username, password='123456')
            if auth_user:
                self.stdout.write(f"✅ Autenticação bem-sucedida: {auth_user.username}")
                self.stdout.write(f"   Empresa: {auth_user.company.name if auth_user.company else 'Nenhuma'}")
                self.stdout.write(f"   Slug da empresa: {auth_user.company.slug if auth_user.company else 'Nenhuma'}")
            else:
                self.stdout.write("❌ Falha na autenticação")
                self.stdout.write("Tentando com senha padrão...")
                auth_user = authenticate(username=test_user.username, password='admin123')
                if auth_user:
                    self.stdout.write("✅ Autenticação com senha 'admin123' bem-sucedida")
                else:
                    self.stdout.write("❌ Falha na autenticação com senha padrão")
