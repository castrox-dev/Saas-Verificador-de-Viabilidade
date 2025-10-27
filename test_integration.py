#!/usr/bin/env python
"""
Script de teste para verificar a integração Django-Flask
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from core.models import Company, CTOMapFile, CustomUser
from core.verificador_service import VerificadorFlaskService, VerificadorIntegrationManager

def test_integration():
    """Testa a integração completa"""
    
    print("=== TESTE DE INTEGRACAO DJANGO-FLASK ===")
    
    # 1. Verificar dados no banco
    print("\n1. Verificando dados no banco:")
    companies = Company.objects.all()
    print(f"   Empresas: {companies.count()}")
    
    files = CTOMapFile.objects.all()
    print(f"   Arquivos CTO: {files.count()}")
    
    for company in companies:
        company_files = files.filter(company=company).count()
        print(f"   - {company.name}: {company_files} arquivos")
    
    # 2. Testar status do Flask
    print("\n2. Testando status do Flask:")
    flask_status = VerificadorFlaskService.verificar_status_flask()
    print(f"   Status: {flask_status['status']}")
    
    if flask_status['status'] == 'offline':
        print("   AVISO: Flask esta offline. Inicie com: cd verificador_flask && python ftth_kml_app.py")
        return False
    
    # 3. Testar verificação de coordenadas
    print("\n3. Testando verificação de coordenadas:")
    try:
        company = companies.first()
        user = CustomUser.objects.filter(company=company).first()
        
        if not user:
            print("   ERRO: Nenhum usuário encontrado para a empresa")
            return False
        
        result = VerificadorFlaskService.verificar_coordenadas(
            lat=-22.9068,
            lon=-43.1729,
            company=company,
            user=user
        )
        
        if result.get('success'):
            print("   OK: Verificação de coordenadas funcionando")
            print(f"   Score: {result.get('viability_score', 'N/A')}")
        else:
            print(f"   ERRO: {result.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # 4. Testar upload de arquivo
    print("\n4. Testando upload de arquivo:")
    try:
        if files.exists():
            test_file = files.first()
            print(f"   Arquivo de teste: {test_file.file_name}")
            
            # Simular análise do arquivo
            result = VerificadorFlaskService.verificar_arquivo(
                uploaded_file=test_file.file,
                company=test_file.company,
                user=test_file.uploaded_by
            )
            
            if result.get('success'):
                print("   OK: Análise de arquivo funcionando")
            else:
                print(f"   ERRO: {result.get('error', 'Erro desconhecido')}")
        else:
            print("   AVISO: Nenhum arquivo para testar")
            
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # 5. Estatísticas da integração
    print("\n5. Estatísticas da integração:")
    stats = VerificadorIntegrationManager.obter_estatisticas_integracao()
    print(f"   Flask online: {stats.get('integration_active', False)}")
    print(f"   Arquivos processados: {stats.get('django_stats', {}).get('processed_files', 0)}")
    print(f"   Taxa de processamento: {stats.get('django_stats', {}).get('processing_rate', 0):.1f}%")
    
    print("\n=== TESTE CONCLUIDO ===")
    return True

if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
