from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import os

class Company(models.Model):
    """Modelo para representar as empresas clientes"""
    name = models.CharField(max_length=200, verbose_name="Nome da Empresa")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug", help_text="URL amigável para a empresa")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    email = models.EmailField(verbose_name="E-mail da Empresa")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    address = models.TextField(blank=True, verbose_name="Endereço")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Garantir que o slug seja único
            original_slug = self.slug
            counter = 1
            while Company.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    """Modelo customizado de usuário com roles e empresa"""
    
    USER_ROLES = [
        ('RM', 'Administrador RM'),  # Você e o Bone
        ('COMPANY_ADMIN', 'Administrador da Empresa'),  # Admin da empresa cliente
        ('COMPANY_USER', 'Usuário da Empresa'),  # Usuário comum da empresa
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=USER_ROLES, 
        default='COMPANY_USER',
        verbose_name="Função"
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='users',
        verbose_name="Empresa"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Superusuários não precisam seguir as regras de empresa
        if self.is_superuser:
            return
        
        # NOTA: Validações de empresa/role são feitas no formulário
        # O modelo apenas ajusta os dados no save() para garantir consistência
        # Não lançar ValidationError aqui para evitar conflitos com o formulário
        
    def save(self, *args, **kwargs):
        # Ajustar dados antes de validar
        # IMPORTANTE: Superusuários sempre mantêm seus privilégios, independente do role
        if self.is_superuser:
            # Superusuários podem ter qualquer role e manter is_superuser=True
            # Não remover is_superuser nem is_staff de superusuários
            if self.role == 'RM':
                # RM não deve ter empresa associada
                self.company_id = None
                # RM pode acessar áreas administrativas do sistema
                if not self.is_staff:
                    self.is_staff = True
        elif self.role == 'RM':
            # RM não deve ter empresa associada
            self.company_id = None
            # RM pode acessar áreas administrativas do sistema
            if not self.is_staff:
                self.is_staff = True
            # Não forçamos superuser aqui; fica a cargo de seed/gestão
        else:
            # Usuários de empresas nunca devem ser superuser, nem staff global
            # Mas apenas se não forem superusuários (já verificado acima)
            if not self.is_superuser:
                # Apenas remover is_staff se não for superuser
                if self.is_staff:
                    self.is_staff = False
        
        # Não chamar clean() aqui para evitar validações que já foram feitas no formulário
        # O formulário já validou role/company, então apenas salvar
        # Se houver erro de validação básica do Django (email único, etc.), deixar passar
        super().save(*args, **kwargs)

    @property
    def is_rm_admin(self):
        """Verifica se é administrador RM"""
        return self.role == 'RM' or self.is_superuser

    @property
    def is_company_admin(self):
        """Verifica se é administrador da empresa"""
        return self.role == 'COMPANY_ADMIN'

    @property
    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.is_rm_admin or self.is_company_admin

    @property
    def can_upload_maps(self):
        """Verifica se pode fazer upload de mapas"""
        return self.is_rm_admin or self.role in ['COMPANY_ADMIN', 'COMPANY_USER']

    def get_full_name(self):
        """Retorna nome completo ou username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __str__(self):
        if self.company:
            return f"{self.get_full_name() or self.username} - {self.company.name}"
        return self.get_full_name() or self.username

class CTOMapFile(models.Model):
    """Modelo para arquivos de mapas CTO"""
    
    FILE_TYPES = [
        ('kml', 'KML'),
        ('kmz', 'KMZ'),
        ('csv', 'CSV'),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    file = models.FileField(upload_to="cto_maps/", verbose_name="Arquivo")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='csv', verbose_name="Tipo de Arquivo")
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='cto_maps',
        verbose_name="Empresa"
    )
    uploaded_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='uploaded_maps',
        verbose_name="Enviado por"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Enviado em")
    
    # Status de processamento
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS, 
        default='pending',
        verbose_name="Status de Processamento"
    )
    is_processed = models.BooleanField(default=False, verbose_name="Processado")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Processado em")
    
    # Resultados da análise Flask
    analysis_id = models.CharField(max_length=100, blank=True, verbose_name="ID da Análise")
    viability_score = models.IntegerField(null=True, blank=True, verbose_name="Score de Viabilidade")
    processing_time = models.FloatField(null=True, blank=True, verbose_name="Tempo de Processamento (s)")
    
    # Dados da análise (JSON)
    analysis_results = models.JSONField(default=dict, blank=True, verbose_name="Resultados da Análise")
    issues_found = models.JSONField(default=list, blank=True, verbose_name="Problemas Encontrados")
    recommendations = models.JSONField(default=list, blank=True, verbose_name="Recomendações")
    
    # Metadados do arquivo
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="Tamanho do Arquivo (bytes)")
    coordinates_count = models.IntegerField(null=True, blank=True, verbose_name="Número de Coordenadas")
    
    # Campos de auditoria
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Mapa CTO"
        verbose_name_plural = "Mapas CTO"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'processing_status']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
            models.Index(fields=['file_type', 'is_processed']),
        ]

    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Verificar se o usuário pode fazer upload (exceto RM Admins e superusers)
        if self.uploaded_by:
            is_rm_admin = getattr(self.uploaded_by, 'is_rm_admin', False)
            is_superuser = getattr(self.uploaded_by, 'is_superuser', False)
            is_company_admin = getattr(self.uploaded_by, 'is_company_admin', False)
            
            # RM Admins, superusers e Company Admins sempre podem fazer upload
            if not (is_rm_admin or is_superuser or is_company_admin):
                if not self.uploaded_by.can_upload_maps:
                    raise ValidationError("Usuário não tem permissão para fazer upload de mapas.")
        
        # Verificar se o usuário pertence à empresa (exceto RM Admins e superusers)
        if self.uploaded_by and self.company:
            is_rm_admin = getattr(self.uploaded_by, 'is_rm_admin', False)
            is_superuser = getattr(self.uploaded_by, 'is_superuser', False)
            
            # RM Admins e superusers podem fazer upload para qualquer empresa
            if not (is_rm_admin or is_superuser):
                if not self.uploaded_by.company or self.uploaded_by.company != self.company:
                    raise ValidationError("Usuário não pertence à empresa especificada.")
        
        # Determinar tipo de arquivo automaticamente baseado no nome do arquivo
        # Sempre detectar baseado no nome real, mesmo se file_type já estiver definido
        if self.file:
            file_name = self.file.name.lower()
            # Detectar extensão do arquivo
            if file_name.endswith('.kml'):
                self.file_type = 'kml'
            elif file_name.endswith('.kmz'):
                self.file_type = 'kmz'
            elif file_name.endswith('.csv'):
                self.file_type = 'csv'
            elif file_name.endswith('.xls'):
                self.file_type = 'xls'
            elif file_name.endswith('.xlsx'):
                self.file_type = 'xlsx'
            # Se não detectou nenhuma extensão conhecida e file_type está vazio, usar default
            elif not self.file_type:
                self.file_type = 'csv'  # Fallback para o default
    
    def save(self, *args, **kwargs):
        self.clean()
        
        # Calcular tamanho do arquivo
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                pass
        
        super().save(*args, **kwargs)
    
    def get_file_size_mb(self):
        """Retorna o tamanho do arquivo em MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_viability_status(self):
        """Retorna o status de viabilidade baseado no score"""
        if self.viability_score is None:
            return "Não analisado"
        
        if self.viability_score >= 80:
            return "Viável"
        elif self.viability_score >= 60:
            return "Viabilidade Limitada"
        else:
            return "Sem Viabilidade"
    
    def get_viability_color(self):
        """Retorna a cor do status de viabilidade"""
        if self.viability_score is None:
            return "#6c757d"  # Cinza
        
        if self.viability_score >= 80:
            return "#28a745"  # Verde
        elif self.viability_score >= 60:
            return "#ffc107"  # Amarelo
        else:
            return "#dc3545"  # Vermelho
    
    @property
    def file_name(self):
        """Retorna apenas o nome do arquivo"""
        return os.path.basename(self.file.name) if self.file else ""

    def __str__(self):
        return f"{self.description or os.path.basename(self.file.name)} - {self.company.name}"


class Ticket(models.Model):
    """Modelo para tickets de suporte"""
    
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
    ]
    
    PRIORITY_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="Título")
    description = models.TextField(verbose_name="Descrição")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberto',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Prioridade"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Empresa"
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='created_tickets',
        verbose_name="Criado por"
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name="Atendido por"
    )
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número do Ticket",
        help_text="Gerado automaticamente"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resolvido em")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fechado em")
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['ticket_number']),
        ]
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        import time
        
        # Gerar número do ticket se não existir
        if not self.ticket_number:
            prefix = "TKT"
            timestamp = timezone.now().strftime("%Y%m%d")
            
            # Tentar contar tickets do dia de forma segura
            count = 0
            try:
                today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Se já tem ID, excluir da contagem para evitar duplicação
                if self.pk:
                    count = Ticket.objects.filter(
                        created_at__gte=today_start,
                        created_at__lte=today_end
                    ).exclude(pk=self.pk).count()
                else:
                    # Para novos tickets, contar apenas os já salvos hoje
                    count = Ticket.objects.filter(
                        created_at__gte=today_start,
                        created_at__lte=today_end
                    ).count()
            except Exception as e:
                # Se houver erro ao contar, usar apenas timestamp
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro ao contar tickets: {str(e)}")
                count = 0
            
            # Tentar gerar número único
            max_attempts = 10
            attempt = 0
            generated = False
            
            while attempt < max_attempts:
                try:
                    ticket_number = f"{prefix}-{timestamp}-{str(count + 1 + attempt).zfill(4)}"
                    # Verificar se já existe
                    if self.pk:
                        exists = Ticket.objects.filter(ticket_number=ticket_number).exclude(pk=self.pk).exists()
                    else:
                        exists = Ticket.objects.filter(ticket_number=ticket_number).exists()
                    
                    if not exists:
                        self.ticket_number = ticket_number
                        generated = True
                        break
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Erro ao verificar ticket_number: {str(e)}")
                    break
                
                attempt += 1
            
            # Fallback: usar timestamp com microsegundos se não conseguiu gerar
            if not generated:
                unique_suffix = str(int(time.time() * 1000000))[-4:]
                self.ticket_number = f"{prefix}-{timestamp}-{unique_suffix}"
        
        # Atualizar timestamps baseado no status
        if self.status == 'resolvido' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        if self.status == 'fechado' and not self.closed_at:
            self.closed_at = timezone.now()
        
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            # Log do erro antes de relançar
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Erro ao salvar ticket: {str(e)}")
            raise
    
    def get_status_color(self):
        """Retorna a cor do status"""
        colors = {
            'aberto': '#007bff',  # Azul
            'em_andamento': '#ffc107',  # Amarelo
            'aguardando_cliente': '#fd7e14',  # Laranja
            'resolvido': '#28a745',  # Verde
            'fechado': '#6c757d',  # Cinza
        }
        return colors.get(self.status, '#6c757d')
    
    def get_priority_color(self):
        """Retorna a cor da prioridade"""
        colors = {
            'baixa': '#6c757d',  # Cinza
            'normal': '#007bff',  # Azul
            'alta': '#ffc107',  # Amarelo
            'urgente': '#dc3545',  # Vermelho
        }
        return colors.get(self.priority, '#6c757d')
    
    def get_last_message(self):
        """Retorna a última mensagem do ticket"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Retorna quantidade de mensagens não lidas para o usuário"""
        if user == self.created_by:
            # Para o criador, contar mensagens enviadas por RM/atendentes
            return self.messages.filter(
                sent_by__role='RM',
                read=False
            ).count()
        elif user.is_rm_admin:
            # Para RM, contar mensagens enviadas pelo cliente
            return self.messages.filter(
                sent_by=self.created_by,
                read=False
            ).count()
        return 0
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title}"


class TicketMessage(models.Model):
    """Modelo para mensagens do ticket (chat)"""
    
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Ticket"
    )
    message = models.TextField(verbose_name="Mensagem")
    sent_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ticket_messages',
        verbose_name="Enviado por"
    )
    read = models.BooleanField(default=False, verbose_name="Lido")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lido em")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Mensagem do Ticket"
        verbose_name_plural = "Mensagens dos Tickets"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['sent_by', 'created_at']),
            models.Index(fields=['read']),
        ]
    
    def mark_as_read(self, user):
        """Marca a mensagem como lida"""
        if not self.read and self.sent_by != user:
            from django.utils import timezone
            self.read = True
            self.read_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"Mensagem {self.id} - Ticket {self.ticket.ticket_number}"

# -----------------------------------------------------------------------------
# Controle opcional de sessão única por usuário
# -----------------------------------------------------------------------------
# Quando quiser garantir que apenas uma sessão permaneça ativa por usuário
# (último login derruba logins anteriores), descomente o bloco abaixo e execute
# `python manage.py makemigrations` seguido de `python manage.py migrate`.
#
# from django.contrib.auth import get_user_model
#
# class UserSession(models.Model):
#     user = models.OneToOneField(
#         get_user_model(),
#         on_delete=models.CASCADE,
#         related_name='active_session'
#     )
#     session_key = models.CharField(max_length=40, blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.user} - {self.session_key}"