from django import forms
from django.forms.widgets import FileInput

class MultipleFileInput(FileInput):
    """Widget personalizado para manejar múltiples archivos"""
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': True})
        super().__init__(attrs)
    
    def value_from_datadict(self, data, files, name):
        """Obtiene múltiples archivos del request"""
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return files.get(name)

class MultipleFileField(forms.FileField):
    """Campo personalizado para manejar múltiples archivos"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Si no hay archivos, retornar lista vacía
        if not data:
            return []
        
        # Si es un solo archivo, convertir a lista
        if not isinstance(data, list):
            data = [data]
        
        # Validar cada archivo individualmente
        cleaned_files = []
        for file in data:
            cleaned_file = super().clean(file, initial)
            if cleaned_file:
                cleaned_files.append(cleaned_file)
        
        return cleaned_files
