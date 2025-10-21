from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from apps.companies.models import Company

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class AdminUserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLES, required=True)
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        help_text="Requerido para empleados y administradores de empresa"
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'company', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company')
        
        # Validate that employees and company admins have a company assigned
        if role in ['EMPLOYEE', 'COMPANY_ADMIN'] and not company:
            raise forms.ValidationError("Los empleados y administradores de empresa deben tener una empresa asignada.")
        
        # Technicians and superadmins don't need a company
        if role in ['TECHNICIAN', 'SUPERADMIN'] and company:
            cleaned_data['company'] = None
            
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.company = self.cleaned_data.get('company')
        if commit:
            user.save()
        return user

class AdminUserEditForm(forms.ModelForm):
    """Formulario para editar usuarios existentes (sin cambiar contraseña)"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLES, required=True)
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        help_text="Requerido para empleados y administradores de empresa"
    )
    is_active = forms.BooleanField(
        required=False,
        help_text="Desmarcar para desactivar el usuario"
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'company', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company')
        
        if role in ['EMPLOYEE', 'COMPANY_ADMIN'] and not company:
            raise forms.ValidationError("Los empleados y administradores de empresa deben tener una empresa asignada.")
        
        if role in ['TECHNICIAN', 'SUPERADMIN'] and company:
            cleaned_data['company'] = None
            
        return cleaned_data

class AdminPasswordChangeForm(forms.Form):
    """Formulario para que el admin cambie la contraseña de un usuario"""
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Mínimo 8 caracteres"
    )
    new_password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Ingresa la misma contraseña para verificación"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        return cleaned_data

class UserPasswordChangeForm(forms.Form):
    """Formulario para que los usuarios cambien su propia contraseña"""
    current_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ingresa tu contraseña actual'
        }),
        help_text="Por seguridad, debes ingresar tu contraseña actual"
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Mínimo 8 caracteres'
        }),
        help_text="Mínimo 8 caracteres, debe incluir letras y números"
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Repite la nueva contraseña'
        }),
        help_text="Ingresa la misma contraseña para verificación"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("La contraseña actual es incorrecta.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        return cleaned_data
    
    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user
