from django.db import models
from django.core.cache import cache
import json


class GeocodingCache(models.Model):
    """Cache de geocodificação persistente"""
    endereco = models.CharField(max_length=500, unique=True, db_index=True)
    lat = models.FloatField()
    lng = models.FloatField()
    endereco_completo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cache de Geocodificação'
        verbose_name_plural = 'Cache de Geocodificações'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.endereco[:50]}... ({self.lat}, {self.lng})"
    
    def to_dict(self):
        return {
            'lat': self.lat,
            'lng': self.lng,
            'endereco_completo': self.endereco_completo
        }


class CTOFile(models.Model):
    """Model para armazenar informações sobre arquivos de CTOs"""
    TIPO_CHOICES = [
        ('kml', 'KML'),
        ('kmz', 'KMZ'),
        ('csv', 'CSV'),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
    ]
    
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    caminho = models.FilePathField(path='', max_length=1000)
    total_pontos = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Arquivo CTO'
        verbose_name_plural = 'Arquivos CTO'
        unique_together = ['nome', 'tipo']
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.tipo}) - {self.total_pontos} pontos"


class ViabilidadeCache(models.Model):
    """Cache de verificações de viabilidade - separado por empresa e mapas ativos"""
    lat = models.FloatField()
    lon = models.FloatField()
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='viability_caches',
        null=False,  # Obrigatório - sempre deve ter empresa
        verbose_name="Empresa"
    )
    mapas_hash = models.CharField(
        max_length=500,
        blank=True,
        default='',
        db_index=True,
        help_text="Hash dos IDs dos mapas ativos quando a verificação foi feita"
    )
    resultado = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cache de Viabilidade'
        verbose_name_plural = 'Cache de Viabilidades'
        unique_together = [['lat', 'lon', 'company', 'mapas_hash']]  # Cache único por coordenada, empresa E mapas ativos
        indexes = [
            models.Index(fields=['lat', 'lon', 'company', 'mapas_hash']),
        ]
    
    def __str__(self):
        status = self.resultado.get('viabilidade', {}).get('status', 'N/A')
        company_name = self.company.name if self.company else 'N/A'
        mapas_info = f" - {len(self.mapas_hash.split(','))} mapa(s)" if self.mapas_hash else ""
        return f"({self.lat:.6f}, {self.lon:.6f}) - {company_name}{mapas_info} - {status}"

