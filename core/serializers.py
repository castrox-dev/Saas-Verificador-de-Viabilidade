"""
Serializers para API REST
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, CTOMapFile

User = get_user_model()

class CompanySerializer(serializers.ModelSerializer):
    """Serializer para Company"""
    user_count = serializers.SerializerMethodField()
    map_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'email', 'phone', 'address',
            'created_at', 'user_count', 'map_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_user_count(self, obj):
        return obj.customuser_set.count()
    
    def get_map_count(self, obj):
        return obj.ctomapfile_set.count()

class UserSerializer(serializers.ModelSerializer):
    """Serializer para User"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'role', 'is_active', 'company',
            'company_name', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class CTOMapFileSerializer(serializers.ModelSerializer):
    """Serializer para CTOMapFile"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = CTOMapFile
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'file_size_mb', 'uploaded_at', 'company', 'company_name',
            'uploaded_by', 'uploaded_by_name', 'status'
        ]
        read_only_fields = ['id', 'uploaded_at']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0

class CompanyStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de empresa"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_maps = serializers.IntegerField()
    maps_this_month = serializers.IntegerField()
    last_activity = serializers.DateTimeField(allow_null=True)

class MapStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de mapas"""
    total = serializers.IntegerField()
    this_month = serializers.IntegerField()
    this_week = serializers.IntegerField()
    by_type = serializers.ListField()

class UserStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de usuários"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    inactive = serializers.IntegerField()
    by_role = serializers.ListField()
    recent_registrations = serializers.IntegerField()
