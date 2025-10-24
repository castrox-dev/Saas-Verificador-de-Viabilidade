"""
API REST para RM Systems SaaS
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Company, CTOMapFile
from .serializers import CompanySerializer, CTOMapFileSerializer, UserSerializer
from .permissions import IsRMAdmin, IsCompanyAdmin

User = get_user_model()

class CompanyViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de empresas"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsRMAdmin]

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Estatísticas da empresa"""
        company = self.get_object()
        
        stats = {
            'total_users': User.objects.filter(company=company).count(),
            'active_users': User.objects.filter(company=company, is_active=True).count(),
            'total_maps': CTOMapFile.objects.filter(company=company).count(),
            'maps_this_month': CTOMapFile.objects.filter(
                company=company,
                uploaded_at__gte=timezone.now().replace(day=1)
            ).count(),
            'last_activity': CTOMapFile.objects.filter(company=company)
                .order_by('-uploaded_at').first()
        }
        
        return Response(stats)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Usuários da empresa"""
        company = self.get_object()
        users = User.objects.filter(company=company)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class CTOMapFileViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de mapas CTO"""
    queryset = CTOMapFile.objects.all()
    serializer_class = CTOMapFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrar por empresa do usuário"""
        user = self.request.user
        if user.is_rm_admin:
            return CTOMapFile.objects.all()
        elif user.company:
            return CTOMapFile.objects.filter(company=user.company)
        return CTOMapFile.objects.none()

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """Mapas agrupados por empresa"""
        if not request.user.is_rm_admin:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)
        
        companies = Company.objects.annotate(
            map_count=Count('ctomapfile')
        ).order_by('-map_count')
        
        data = []
        for company in companies:
            data.append({
                'company': CompanySerializer(company).data,
                'map_count': company.map_count,
                'last_upload': CTOMapFile.objects.filter(company=company)
                    .order_by('-uploaded_at').first()
            })
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Mapas recentes"""
        queryset = self.get_queryset().order_by('-uploaded_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas de mapas"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'this_month': queryset.filter(
                uploaded_at__gte=timezone.now().replace(day=1)
            ).count(),
            'this_week': queryset.filter(
                uploaded_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'by_type': queryset.values('file_type').annotate(
                count=Count('id')
            ).order_by('-count')
        }
        
        return Response(stats)

class UserViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de usuários"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrar por empresa do usuário"""
        user = self.request.user
        if user.is_rm_admin:
            return User.objects.all()
        elif user.is_company_admin and user.company:
            return User.objects.filter(company=user.company)
        return User.objects.none()

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """Usuários agrupados por empresa"""
        if not request.user.is_rm_admin:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)
        
        companies = Company.objects.annotate(
            user_count=Count('customuser')
        ).order_by('-user_count')
        
        data = []
        for company in companies:
            data.append({
                'company': CompanySerializer(company).data,
                'user_count': company.user_count,
                'active_users': User.objects.filter(
                    company=company, is_active=True
                ).count()
            })
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas de usuários"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'inactive': queryset.filter(is_active=False).count(),
            'by_role': queryset.values('role').annotate(
                count=Count('id')
            ).order_by('-count'),
            'recent_registrations': queryset.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count()
        }
        
        return Response(stats)
