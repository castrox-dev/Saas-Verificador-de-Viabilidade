from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_rm_superusers(apps, schema_editor):
    CustomUser = apps.get_model('core', 'CustomUser')

    users_data = [
        {
            'username': 'castrox.rmsys.com',
            'email': 'castrox@rmsys.com',
            'password': 'castro!2007#',
        },
        {
            'username': 'bone.rmsys.com',
            'email': 'bone@rmsys.com',
            'password': 'bone!1999#',
        },
    ]

    for data in users_data:
        user, created = CustomUser.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'role': 'RM',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
                'password': make_password(data['password']),
                'company_id': None,
            }
        )
        if not created:
            user.email = data['email']
            user.role = 'RM'
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.password = make_password(data['password'])
            user.company_id = None
            user.save()


def remove_rm_superusers(apps, schema_editor):
    CustomUser = apps.get_model('core', 'CustomUser')
    CustomUser.objects.filter(username__in=['castrox.rmsys.com', 'bone.rmsys.com']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_add_fibramar_company'),
    ]

    operations = [
        migrations.RunPython(create_rm_superusers, remove_rm_superusers),
    ]