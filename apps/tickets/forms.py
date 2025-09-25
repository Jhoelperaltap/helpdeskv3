from django import forms
from django.contrib.auth import get_user_model
from .models import EscalationRule, EscalationSettings
from apps.companies.models import Company

User = get_user_model()

class EscalationRuleForm(forms.ModelForm):
    class Meta:
        model = EscalationRule
        fields = [
            'company', 'priority', 'level', 'hours_to_escalate', 
            'escalate_to', 'notification_template', 'is_active'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Seleccionar empresa (opcional para regla global)'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'hours_to_escalate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.5',
                'step': '0.5'
            }),
            'escalate_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notification_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Plantilla de notificación personalizada (opcional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios que pueden recibir escalamientos
        self.fields['escalate_to'].queryset = User.objects.filter(
            role__in=['TECHNICIAN', 'SUPERADMIN'],
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
        
        # Agregar opción vacía para empresa (regla global)
        self.fields['company'].empty_label = "Regla Global (todas las empresas)"
        
        # Ayuda contextual
        self.fields['level'].help_text = "Nivel de escalamiento (1 = primer escalamiento)"
        self.fields['hours_to_escalate'].help_text = "Horas sin respuesta antes de escalar"
        self.fields['notification_template'].help_text = "Mensaje personalizado para notificaciones (opcional)"

class EscalationSettingsForm(forms.ModelForm):
    business_days = forms.MultipleChoiceField(
        choices=[
            ('1', 'Lunes'),
            ('2', 'Martes'),
            ('3', 'Miércoles'),
            ('4', 'Jueves'),
            ('5', 'Viernes'),
            ('6', 'Sábado'),
            ('7', 'Domingo'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Días laborales para el escalamiento"
    )
    
    class Meta:
        model = EscalationSettings
        fields = [
            'company', 'enabled', 'business_hours_only', 'business_start_hour',
            'business_end_hour', 'business_days', 'max_escalation_level',
            'auto_assign_on_escalation', 'pause_on_response', 'email_notifications'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'business_hours_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'business_start_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '23'
            }),
            'business_end_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '23'
            }),
            'max_escalation_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'auto_assign_on_escalation': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'pause_on_response': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar opción vacía para empresa (configuración global)
        self.fields['company'].empty_label = "Configuración Global (todas las empresas)"
        
        # Valores por defecto
        if not self.instance.pk:
            self.fields['business_days'].initial = ['1', '2', '3', '4', '5']  # Lunes a Viernes
            self.fields['business_start_hour'].initial = 9
            self.fields['business_end_hour'].initial = 18
            self.fields['max_escalation_level'].initial = 3
        else:
            # Cargar días laborales existentes
            if self.instance.business_days:
                self.fields['business_days'].initial = self.instance.get_business_days_list()
        
        # Ayuda contextual
        self.fields['business_hours_only'].help_text = "Solo escalar durante horario laboral"
        self.fields['max_escalation_level'].help_text = "Nivel máximo de escalamiento permitido"
        self.fields['auto_assign_on_escalation'].help_text = "Asignar automáticamente al usuario del escalamiento"
        self.fields['pause_on_response'].help_text = "Pausar escalamiento cuando hay respuesta"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Guardar días laborales como string separado por comas
        business_days = self.cleaned_data.get('business_days', [])
        instance.business_days = ','.join(business_days) if business_days else ''
        
        if commit:
            instance.save()
        
        return instance
