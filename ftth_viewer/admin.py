from django.contrib import admin
from .models import GeocodingCache, CTOFile, ViabilidadeCache


@admin.register(GeocodingCache)
class GeocodingCacheAdmin(admin.ModelAdmin):
    list_display = ['endereco', 'lat', 'lng', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['endereco', 'endereco_completo']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(CTOFile)
class CTOFileAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'total_pontos', 'ativo', 'created_at']
    list_filter = ['tipo', 'ativo', 'created_at']
    search_fields = ['nome']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nome']


@admin.register(ViabilidadeCache)
class ViabilidadeCacheAdmin(admin.ModelAdmin):
    list_display = ['lat', 'lon', 'status_display', 'distancia_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['lat', 'lon']
    readonly_fields = ['created_at', 'resultado']
    ordering = ['-created_at']
    
    def status_display(self, obj):
        return obj.resultado.get('viabilidade', {}).get('status', 'N/A')
    status_display.short_description = 'Status'
    
    def distancia_display(self, obj):
        return f"{obj.resultado.get('distancia', {}).get('metros', 0):.0f}m"
    distancia_display.short_description = 'Distância'

