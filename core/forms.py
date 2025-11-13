from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
import os
from .models import CTOMapFile, Company, CustomUser
from .security_validators import SecureFileValidator
from .rate_limiting import upload_rate_limit

class CTOMapFileForm(forms.ModelForm):
    class Meta:
        model = CTOMapFile
        fields = ["file", "description", "company"]
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'file-input-hidden',
                'accept': '.xlsx,.xls,.csv,.kml,.kmz',
                'id': 'id_file',
                'style': 'display: none;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Adicione uma descrição para identificar melhor este arquivo...',
                'rows': 3,
                'maxlength': 500
            }),
            'company': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_company'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Por favor, selecione um arquivo.")
        
        # Usar validador seguro
        validator = SecureFileValidator()
        try:
            validator.validate_file(file)
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError("Erro na validação do arquivo. Tente novamente.")
        
        return file
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        
        # Limpar espaços em branco extras
        description = description.strip()
        
        # Validar comprimento
        if len(description) > 500:
            raise ValidationError(
                "Descrição muito longa. "
                "Por favor, use no máximo 500 caracteres."
            )
        
        return description

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'cnpj', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da empresa'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00',
                'maxlength': 18
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@empresa.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo da empresa'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove caracteres não numéricos
            cnpj_numbers = ''.join(filter(str.isdigit, cnpj))
            
            # Valida se tem 14 dígitos
            if len(cnpj_numbers) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos')
            # Formatar no padrão 00.000.000/0000-00
            formatted = f"{cnpj_numbers[:2]}.{cnpj_numbers[2:5]}.{cnpj_numbers[5:8]}/{cnpj_numbers[8:12]}-{cnpj_numbers[12:]}"
            self.cleaned_data['cnpj'] = formatted
            
            # Verifica se já existe outro CNPJ igual (exceto o próprio)
            existing = Company.objects.filter(cnpj=formatted)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Já existe uma empresa com este CNPJ')
        
        return self.cleaned_data.get('cnpj')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError('Informe um e-mail válido.')
        if '@' not in email or email.startswith('@') or email.endswith('@'):
            raise ValidationError('E-mail inválido. Verifique o endereço informado.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) not in (10, 11):
                raise ValidationError('Telefone deve conter DDD + número (10 ou 11 dígitos).')
            ddd = digits[:2]
            if len(digits) == 10:
                number = f"{digits[2:6]}-{digits[6:]}"
            else:
                number = f"{digits[2:7]}-{digits[7:]}"
            formatted = f"({ddd}) {number}"
            self.cleaned_data['phone'] = formatted
        return self.cleaned_data.get('phone', '')

class CustomUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'company', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome de usuário'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos baseado no usuário atual
        if self.current_user:
            if self.current_user.is_rm_admin or self.current_user.is_superuser:
                # RM admin ou superuser podem criar qualquer tipo de usuário
                self.fields['role'].choices = CustomUser.USER_ROLES
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            elif self.current_user.is_company_admin:
                # Admin da empresa só pode criar usuários da empresa
                self.fields['role'].choices = [
                    ('COMPANY_ADMIN', 'Administrador da Empresa'),
                    ('COMPANY_USER', 'Usuário da Empresa')
                ]
                self.fields['company'].queryset = Company.objects.filter(
                    id=self.current_user.company.id
                )
                self.fields['company'].initial = self.current_user.company
                # Remove opção vazia para evitar submissão sem empresa
                self.fields['company'].empty_label = None
            else:
                # Usuários normais não podem criar outros usuários
                raise ValidationError('Sem permissão para criar usuários')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company')
        
        # Superuser pode criar qualquer combinação sem bloqueios de formulário
        if self.current_user and getattr(self.current_user, 'is_superuser', False):
            return cleaned_data
        
        # Validações baseadas no role
        if role == 'RM' and company:
            self.add_error('company', 'Administradores RM não devem ter empresa associada.')
        elif role in ['COMPANY_ADMIN', 'COMPANY_USER'] and not company:
            self.add_error('company', 'Usuários de empresa devem ter uma empresa associada.')
        
        # Validações baseadas no usuário atual
        if self.current_user and self.current_user.is_company_admin:
            if company != self.current_user.company:
                self.add_error('company', 'Você só pode criar usuários para sua empresa.')
            # Garantir que role seja válido para empresa
            if role not in ['COMPANY_ADMIN', 'COMPANY_USER']:
                self.add_error('role', 'Role inválido para usuários de empresa.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        
        # Definir role e company antes de salvar
        user.role = self.cleaned_data.get('role', 'COMPANY_USER')
        user.company = self.cleaned_data.get('company', None)
        
        # Garantir que role e company estejam corretos antes de salvar
        # As validações do clean() do formulário já foram feitas
        # Garantir consistência: RM não deve ter empresa, COMPANY_ADMIN/USER devem ter
        if user.role == 'RM':
            user.company = None
            user.company_id = None
        
        # Salvar o usuário
        # O save() do modelo ajusta os dados automaticamente e não chama clean()
        if commit:
            try:
                user.save()
            except Exception as e:
                # Capturar qualquer erro e adicionar ao formulário
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erro ao salvar usuário: {str(e)}", exc_info=True)
                
                error_message = str(e)
                
                # Tentar identificar o tipo de erro
                if 'unique constraint' in error_message.lower() or 'already exists' in error_message.lower() or 'duplicate key' in error_message.lower():
                    if 'username' in error_message.lower() or 'user' in error_message.lower():
                        self.add_error('username', 'Este nome de usuário já está em uso.')
                    elif 'email' in error_message.lower():
                        self.add_error('email', 'Este e-mail já está em uso.')
                    else:
                        self.add_error(None, 'Este registro já existe no sistema.')
                elif isinstance(e, ValidationError):
                    # Se for ValidationError, tratar adequadamente
                    if hasattr(e, 'error_dict') and e.error_dict:
                        for field, errors in e.error_dict.items():
                            for error in errors:
                                self.add_error(field, error)
                    elif hasattr(e, 'error_list') and e.error_list:
                        for error in e.error_list:
                            self.add_error(None, str(error))
                    else:
                        self.add_error(None, error_message)
                else:
                    # Outro erro - adicionar como erro geral
                    self.add_error(None, f'Erro ao salvar usuário: {error_message}')
                
                # Re-lançar como ValidationError para que a view saiba
                raise ValidationError(f'Erro ao salvar usuário: {error_message}') from e
        
        return user

class CustomUserChangeForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'company', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos baseado no usuário atual
        if self.current_user:
            if self.current_user.is_rm_admin or self.current_user.is_superuser:
                self.fields['role'].choices = CustomUser.USER_ROLES
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            elif self.current_user.is_company_admin:
                self.fields['role'].choices = [
                    ('COMPANY_ADMIN', 'Administrador da Empresa'),
                    ('COMPANY_USER', 'Usuário da Empresa')
                ]
                if self.current_user.company:
                    self.fields['company'].queryset = Company.objects.filter(id=self.current_user.company.id)
                    self.fields['company'].initial = self.current_user.company
                    self.fields['company'].empty_label = None
            else:
                raise ValidationError('Sem permissão para editar usuários')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company')
        
        # Superuser pode editar qualquer combinação
        if self.current_user and getattr(self.current_user, 'is_superuser', False):
            return cleaned_data
        
        if role == 'RM' and company:
            raise ValidationError('Administradores RM não devem ter empresa associada.')
        elif role in ['COMPANY_ADMIN', 'COMPANY_USER'] and not company:
            raise ValidationError('Usuários de empresa devem ter uma empresa associada.')
        
        if self.current_user and self.current_user.is_company_admin:
            if company != self.current_user.company:
                raise ValidationError('Você só pode editar usuários da sua empresa.')
            # Garantir que role seja válido para empresa
            if role not in ['COMPANY_ADMIN', 'COMPANY_USER']:
                raise ValidationError('Role inválido para usuários de empresa.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user