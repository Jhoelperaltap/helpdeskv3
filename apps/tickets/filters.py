import django_filters
from django import forms
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Ticket
from apps.companies.models import Company
from apps.users.models import User

class TicketFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar en título, descripción, referencia o mensajes...',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    status = django_filters.MultipleChoiceFilter(
        choices=Ticket.STATUS,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        })
    )
    
    priority = django_filters.MultipleChoiceFilter(
        choices=Ticket.PRIORITY,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        })
    )
    
    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(),
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    assigned_to = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(role__in=['TECHNICIAN', 'SUPERADMIN']),
        empty_label="Sin asignar / Todos",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    created_at = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    updated_at = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )

    class Meta:
        model = Ticket
        fields = ['search', 'status', 'priority', 'company', 'assigned_to', 'created_at', 'updated_at']

    def filter_search(self, queryset, name, value):
        """
        Búsqueda inteligente con PostgreSQL full-text search y fallback para SQLite
        """
        if not value:
            return queryset
        
        # Detectar si estamos usando PostgreSQL
        from django.conf import settings
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in db_engine:
            search_vector = SearchVector(
                title='A',
                description='B', 
                reference='A',
                messages__content='C'
            )
            search_query = SearchQuery(value)
            
            return queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(
                search=search_query
            ).order_by('-rank', '-updated_at').distinct()
        else:
            # Fallback para SQLite con búsqueda básica
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(reference__icontains=value) |
                Q(messages__content__icontains=value)
            ).distinct()

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        
        if request and request.user.is_authenticated:
            user = request.user
            
            # Filtrar empresas según el rol
            if user.is_superadmin() or user.is_technician():
                # Pueden ver todas las empresas
                pass
            elif user.is_company_admin():
                # Solo su empresa
                self.filters['company'].queryset = Company.objects.filter(id=user.company.id)
            else:
                # Empleados no ven el filtro de empresa
                del self.filters['company']
            
            # Filtrar técnicos asignados
            if user.is_superadmin():
                # Pueden ver todos los técnicos
                pass
            elif user.is_technician():
                # Pueden ver todos los técnicos
                pass
            else:
                # Otros roles ven técnicos limitados
                self.filters['assigned_to'].queryset = User.objects.filter(
                    role__in=['TECHNICIAN', 'SUPERADMIN']
                )
