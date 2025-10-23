from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
import os
from .models import CTOMapFile, Company, CustomUser

class CTOMapFileForm(forms.ModelForm):
    class Meta:
        model = CTOMapFile
        fields = ["file", "description", "company"]
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'file-input-hidden',
                'accept': '.xlsx,.xls,.csv',
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
        
        # Validar extensão do arquivo
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Tipo de arquivo não suportado. "
                f"Por favor, envie arquivos nos formatos: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamanho do arquivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB em bytes
        if file.size > max_size:
            size_mb = round(file.size / (1024 * 1024), 2)
            raise ValidationError(
                f"Arquivo muito grande ({size_mb}MB). "
                f"O tamanho máximo permitido é 10MB."
            )
        
        # Validar nome do arquivo
        if len(file.name) > 100:
            raise ValidationError(
                "Nome do arquivo muito longo. "
                "Por favor, renomeie o arquivo para ter no máximo 100 caracteres."
            )
        
        # Verificar se não contém caracteres especiais problemáticos
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file.name for char in invalid_chars):
            raise ValidationError(
                "Nome do arquivo contém caracteres inválidos. "
                "Por favor, remova os seguintes caracteres: < > : \" | ? *"
            )
        
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
            
            # Verifica se já existe outro CNPJ igual (exceto o próprio)
            existing = Company.objects.filter(cnpj=cnpj)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Já existe uma empresa com este CNPJ')
        
        return cnpj

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
            if self.current_user.is_rm_admin:
                # RM admin pode criar qualquer tipo de usuário
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
                self.fields['company'].widget.attrs['readonly'] = True
            else:
                # Usuários normais não podem criar outros usuários
                raise ValidationError('Sem permissão para criar usuários')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company')
        
        # Validações baseadas no role
        if role == 'RM' and company:
            raise ValidationError('Administradores RM não devem ter empresa associada.')
        elif role in ['COMPANY_ADMIN', 'COMPANY_USER'] and not company:
            raise ValidationError('Usuários de empresa devem ter uma empresa associada.')
        
        # Validações baseadas no usuário atual
        if self.current_user and self.current_user.is_company_admin:
            if company != self.current_user.company:
                raise ValidationError('Você só pode criar usuários para sua empresa.')
        
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