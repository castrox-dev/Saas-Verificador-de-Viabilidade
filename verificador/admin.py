from django.contrib import admin
from .models import GeocodingCache, ViabilidadeCache, CTOFile


@admin.register(GeocodingCache)
class GeocodingCacheAdmin(admin.ModelAdmin):
    list_display = ['endereco', 'lat', 'lng', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['endereco', 'endereco_completo']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(ViabilidadeCache)
class ViabilidadeCacheAdmin(admin.ModelAdmin):
    list_display = ['lat', 'lon', 'status', 'created_at']
    list_filter = ['created_at']
    search_fields = ['lat', 'lon']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def status(self, obj):
        return obj.resultado.get('viabilidade', {}).get('status', 'N/A')
    status.short_description = 'Status'


@admin.register(CTOFile)
class CTOFileAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'total_pontos', 'ativo', 'created_at']
    list_filter = ['tipo', 'ativo', 'created_at']
    search_fields = ['nome']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nome']
# Por enquanto, o verificador não tem modelos próprios
# Ele usa os modelos do core (CTOMapFile)
