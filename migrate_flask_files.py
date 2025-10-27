#!/usr/bin/env python
"""
Script para migrar arquivos CTO do Flask para o banco de dados Django
Cria registros no banco para cada empresa com seus respectivos mapas
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_viabilidade.settings')
django.setup()

from core.models import Company, CTOMapFile, CustomUser
from django.core.files import File
import shutil

def migrate_flask_files():
    """Migra arquivos do Flask para o banco Django"""
    
    print("=== MIGRACAO DE ARQUIVOS FLASK PARA DJANGO ===")
    
    # Caminhos dos arquivos Flask
    flask_maps_dir = Path("verificador_flask/Mapas")
    
    if not flask_maps_dir.exists():
        print("ERRO: Diretorio de mapas Flask nao encontrado!")
        return
    
    # Obter empresas existentes
    companies = Company.objects.all()
    if not companies.exists():
        print("ERRO: Nenhuma empresa encontrada no banco!")
        return
    
    print(f"Empresas encontradas: {companies.count()}")
    for company in companies:
        print(f"   - {company.name} (slug: {company.slug})")
    
    # Criar usuário da empresa para uploads se não existir
    company = companies.first()  # Usar primeira empresa
    admin_user, created = CustomUser.objects.get_or_create(
        username='migration_user',
        defaults={
            'role': 'COMPANY_ADMIN',
            'company': company,
            'is_staff': False,
            'is_active': True,
            'first_name': 'Migration',
            'last_name': 'User'
        }
    )
    
    if created:
        admin_user.set_password('migration123')
        admin_user.save()
        print(f"Usuario de migracao criado: {admin_user.username} para {company.name}")
    
    # Processar cada tipo de arquivo
    file_types = {
        'kml': flask_maps_dir / 'kml',
        'kmz': flask_maps_dir / 'kmz', 
        'csv': flask_maps_dir / 'csv',
        'xls': flask_maps_dir / 'xls',
        'xlsx': flask_maps_dir / 'xlsx'
    }
    
    total_migrated = 0
    
    for file_type, file_dir in file_types.items():
        if not file_dir.exists():
            print(f"AVISO: Diretorio {file_type} nao encontrado")
            continue
            
        files = list(file_dir.glob(f'*.{file_type}'))
        if not files:
            print(f"AVISO: Nenhum arquivo {file_type} encontrado")
            continue
            
        print(f"\nProcessando arquivos {file_type.upper()} ({len(files)} arquivos)")
        
        for file_path in files:
            try:
                # Determinar empresa baseada no nome do arquivo ou distribuir entre empresas
                company = companies.first()  # Por enquanto, usar primeira empresa
                
                # Verificar se arquivo já foi migrado
                existing_file = CTOMapFile.objects.filter(
                    file__icontains=file_path.name,
                    company=company
                ).first()
                
                if existing_file:
                    print(f"   PULADO: {file_path.name} ja migrado")
                    continue
                
                # Criar registro no banco
                with open(file_path, 'rb') as f:
                    django_file = File(f, name=file_path.name)
                    
                    cto_file = CTOMapFile.objects.create(
                        file=django_file,
                        description=f"Arquivo migrado: {file_path.stem}",
                        file_type=file_type,
                        company=company,
                        uploaded_by=admin_user,
                        processing_status='pending',
                        file_size=file_path.stat().st_size
                    )
                
                print(f"   OK: {file_path.name} migrado para {company.name}")
                total_migrated += 1
                
            except Exception as e:
                print(f"   ERRO: Erro ao migrar {file_path.name}: {e}")
    
    print(f"\nMigracao concluida!")
    print(f"Total de arquivos migrados: {total_migrated}")
    
    # Estatísticas finais
    total_files = CTOMapFile.objects.count()
    print(f"Total de arquivos no banco: {total_files}")
    
    for company in companies:
        company_files = CTOMapFile.objects.filter(company=company).count()
        print(f"   - {company.name}: {company_files} arquivos")

def create_company_specific_directories():
    """Cria diretorios especificos para cada empresa"""
    
    print("\n=== CRIANDO DIRETORIOS POR EMPRESA ===")
    
    companies = Company.objects.all()
    base_dir = Path("media")
    base_dir.mkdir(exist_ok=True)
    
    cto_maps_dir = base_dir / "cto_maps"
    cto_maps_dir.mkdir(exist_ok=True)
    
    for company in companies:
        company_dir = cto_maps_dir / company.slug
        company_dir.mkdir(exist_ok=True)
        
        # Criar subdiretorios por tipo
        for file_type in ['kml', 'kmz', 'csv', 'xls', 'xlsx']:
            type_dir = company_dir / file_type
            type_dir.mkdir(exist_ok=True)
        
        print(f"OK: Diretorio criado: {company_dir}")

if __name__ == "__main__":
    try:
        migrate_flask_files()
        create_company_specific_directories()
        
        print("\nProximos passos:")
        print("1. Iniciar o servidor Flask: cd verificador_flask && python ftth_kml_app.py")
        print("2. Testar integracao no Django")
        print("3. Configurar uploads por empresa")
        
    except Exception as e:
        print(f"ERRO na migracao: {e}")
        import traceback
        traceback.print_exc()
