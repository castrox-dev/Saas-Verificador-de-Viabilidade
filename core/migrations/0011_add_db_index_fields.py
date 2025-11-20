# Generated migration for db_index fields
# Esta migração adiciona índices para campos que têm db_index=True
# mas que podem não ter sido criados nas migrações anteriores

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_performance_indexes'),
    ]

    operations = [
        # Adicionar índices para campos com db_index=True
        # Nota: ForeignKeys (company, uploaded_by) já criam índices automaticamente
        # mas vamos adicionar explicitamente para garantir consistência
        
        # CustomUser.created_at (db_index=True)
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['created_at'], name='core_customuser_created_at_idx'),
        ),
        
        # CTOMapFile.uploaded_at (db_index=True)
        migrations.AddIndex(
            model_name='ctomapfile',
            index=models.Index(fields=['uploaded_at'], name='core_ctomapfile_uploaded_at_idx'),
        ),
    ]

