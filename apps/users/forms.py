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
