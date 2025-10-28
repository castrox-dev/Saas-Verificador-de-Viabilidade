#!/usr/bin/env python
"""
Script de teste para verificar o verificador Django nativo
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from core.models import Company, CTOMapFile, CustomUser
from core.verificador_service import VerificadorService, VerificadorIntegrationManager
from verificador.services import VerificadorService as VerificadorAppService

def test_verificador():
    """Testa o verificador Django nativo"""
    
    print("=== TESTE DO VERIFICADOR DJANGO ===")
    
    # 1. Verificar dados no banco
    print("\n1. Verificando dados no banco:")
    companies = Company.objects.all()
    print(f"   Empresas: {companies.count()}")
    
    files = CTOMapFile.objects.all()
    print(f"   Arquivos CTO: {files.count()}")
    
    for company in companies:
        company_files = files.filter(company=company).count()
        print(f"   - {company.name}: {company_files} arquivos")
    
    # 2. Testar status do serviço
    print("\n2. Testando status do verificador:")
    status = VerificadorService.verificar_status_flask()
    print(f"   Status: {status['status']}")
    print(f"   Serviço: {status.get('service', 'N/A')}")
    
    # 3. Testar verificação de coordenadas
    print("\n3. Testando verificação de coordenadas:")
    try:
        company = companies.first()
        if not company:
            print("   AVISO: Nenhuma empresa encontrada")
            return False
            
        user = CustomUser.objects.filter(company=company).first()
        if not user:
            # Criar usuário temporário se não existir
            print("   AVISO: Criando usuário de teste...")
            user = CustomUser.objects.create_user(
                username='test_user',
                email='test@example.com',
                password='test123',
                company=company,
                role='COMPANY_USER'
            )
        
        result = VerificadorService.verificar_coordenadas(
            lat=-22.9068,
            lon=-43.1729,
            company=company,
            user=user
        )
        
        if result.get('success'):
            print("   ✅ Verificação de coordenadas funcionando")
            results = result.get('results', {})
            if results:
                print(f"   Status de viabilidade: {results.get('viabilidade', {}).get('status', 'N/A')}")
                print(f"   Distância: {results.get('distancia', {}).get('metros', 'N/A')}m")
        else:
            print(f"   ⚠️  {result.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Estatísticas da integração
    print("\n4. Estatísticas do verificador:")
    stats = VerificadorIntegrationManager.obter_estatisticas_integracao()
    print(f"   Serviço ativo: {stats.get('integration_active', False)}")
    print(f"   Total de arquivos: {stats.get('django_stats', {}).get('total_files', 0)}")
    print(f"   Arquivos processados: {stats.get('django_stats', {}).get('processed_files', 0)}")
    print(f"   Taxa de processamento: {stats.get('django_stats', {}).get('processing_rate', 0):.1f}%")
    
    # 5. Testar leitura de arquivos (se houver)
    print("\n5. Testando leitura de arquivos:")
    try:
        from verificador.file_readers import FileReaderService
        
        if files.exists():
            test_file = files.first()
            if test_file.file and hasattr(test_file.file, 'path'):
                file_path = test_file.file.path
                if os.path.exists(file_path):
                    coords = FileReaderService.ler_arquivo(file_path)
                    print(f"   ✅ Arquivo '{test_file.file_name}' lido com sucesso")
                    print(f"   Coordenadas encontradas: {len(coords)}")
                else:
                    print(f"   ⚠️  Arquivo não encontrado no sistema de arquivos")
            else:
                print("   ⚠️  Arquivo não tem path válido")
        else:
            print("   ⚠️  Nenhum arquivo para testar")
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print("\n=== TESTE CONCLUÍDO ===")
    return True

if __name__ == "__main__":
    try:
        test_verificador()
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
