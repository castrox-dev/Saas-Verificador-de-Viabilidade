from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import AdminSite
from .models import Company, CustomUser, CTOMapFile

class RMOnlyAdminSite(AdminSite):
    site_header = "RM Systems Admin"
    site_title = "RM Admin"
    index_title = "Painel RM"

    def has_permission(self, request):
        user = request.user
        # Permite acesso somente para usuários ativos, staff e com role RM
        return user.is_active and user.is_staff and getattr(user, 'role', None) == 'RM'

# Instância do AdminSite restrita a RM
rm_admin_site = RMOnlyAdminSite(name='rm_admin')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'cnpj', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'cnpj', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'cnpj', 'email', 'phone')
        }),
        ('Endereço', {
            'fields': ('address',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'company', 'is_active']
    list_filter = ['role', 'company', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Customizadas', {
            'fields': ('role', 'company', 'phone')
        }),
        ('Datas Customizadas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_rm_admin:
            return qs
        elif request.user.is_company_admin:
            return qs.filter(company=request.user.company)
        return qs.none()

@admin.register(CTOMapFile)
class CTOMapFileAdmin(admin.ModelAdmin):
    list_display = ['file', 'company', 'uploaded_by', 'uploaded_at', 'is_processed']
    list_filter = ['company', 'is_processed', 'uploaded_at']
    search_fields = ['file', 'description', 'company__name', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'processed_at']
    
    fieldsets = (
        ('Arquivo', {
            'fields': ('file', 'description')
        }),
        ('Associações', {
            'fields': ('company', 'uploaded_by')
        }),
        ('Status', {
            'fields': ('is_processed', 'processed_at')
        }),
        ('Datas', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_rm_admin:
            return qs
        elif request.user.company:
            return qs.filter(company=request.user.company)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            if not obj.uploaded_by:
                obj.uploaded_by = request.user
            if not obj.company and request.user.company:
                obj.company = request.user.company
        super().save_model(request, obj, form, change)

# Registrar modelos também no AdminSite restrito a RM
rm_admin_site.register(Company, CompanyAdmin)
rm_admin_site.register(CustomUser, CustomUserAdmin)
rm_admin_site.register(CTOMapFile, CTOMapFileAdmin)
