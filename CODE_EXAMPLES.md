# Ejemplos de Código - Paginación y Filtros

Este documento muestra ejemplos de código de la implementación de paginación y filtros.

## 1. Vista con Paginación y Filtros

**Archivo:** `apps/tickets/views.py`

```python
from django_filters.views import FilterView

class TicketListView(LoginRequiredMixin, FilterView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    login_url = '/users/login/'
    filterset_class = TicketFilter
    paginate_by = 20  # ← PAGINACIÓN: 20 tickets por página
    
    def get_queryset(self):
        """Obtiene tickets según el rol del usuario"""
        user = self.request.user
        qs = Ticket.objects.select_related('company','created_by','assigned_to')
        
        if user.is_superadmin():
            base_qs = qs  # Ve todos los tickets
        elif user.is_technician():
            base_qs = qs  # Ve todos los tickets
        elif user.is_company_admin():
            base_qs = qs.filter(company=user.company)  # Solo su empresa
        else:  # EMPLOYEE
            base_qs = qs.filter(created_by=user)  # Solo sus tickets
        
        return base_qs.order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        """Agrega estadísticas al contexto"""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Estadísticas en tiempo real
        context['total_count'] = queryset.count()
        context['open_count'] = queryset.filter(status='OPEN').count()
        context['in_progress_count'] = queryset.filter(status='IN_PROGRESS').count()
        context['resolved_count'] = queryset.filter(status='RESOLVED').count()
        context['closed_count'] = queryset.filter(status='CLOSED').count()
        context['high_priority_count'] = queryset.filter(priority='HIGH').count()
        
        # Filtros guardados del usuario
        context['saved_filters'] = SavedFilter.objects.filter(user=self.request.user)
        context['has_active_filters'] = bool(self.request.GET.dict())
        
        return context
```

## 2. Clase de Filtros

**Archivo:** `apps/tickets/filters.py`

```python
import django_filters
from django import forms
from django.db.models import Q

class TicketFilter(django_filters.FilterSet):
    # BÚSQUEDA TEXTUAL
    search = django_filters.CharFilter(
        method='filter_search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar en título, descripción, referencia o mensajes...',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg'
        })
    )
    
    # FILTRO POR ESTADO (Multiple Choice)
    status = django_filters.MultipleChoiceFilter(
        choices=Ticket.STATUS,  # [('OPEN','Abierto'), ('IN_PROGRESS','En Progreso'), ...]
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'})
    )
    
    # FILTRO POR PRIORIDAD (Multiple Choice)
    priority = django_filters.MultipleChoiceFilter(
        choices=Ticket.PRIORITY,  # [('LOW','Baja'), ('MEDIUM','Media'), ('HIGH','Alta')]
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'})
    )
    
    # FILTRO POR EMPRESA
    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(),
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    # FILTRO POR TÉCNICO ASIGNADO
    assigned_to = django_filters.ModelChoiceFilter(
        queryset=User.objects.filter(role__in=['TECHNICIAN', 'SUPERADMIN']),
        empty_label="Sin asignar / Todos",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    # FILTROS POR FECHA
    created_at = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-lg'
        })
    )
    
    updated_at = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-lg'
        })
    )

    class Meta:
        model = Ticket
        fields = ['search', 'status', 'priority', 'company', 'assigned_to', 
                  'created_at', 'updated_at']

    def filter_search(self, queryset, name, value):
        """
        Búsqueda inteligente con PostgreSQL full-text search y fallback para SQLite
        """
        if not value:
            return queryset
        
        from django.conf import settings
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in db_engine:
            # PostgreSQL Full-Text Search
            from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
            
            search_vector = SearchVector(
                'title', weight='A',
                'description', weight='B', 
                'reference', weight='A',
                'messages__content', weight='C'
            )
            search_query = SearchQuery(value)
            
            return queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(
                search=search_query
            ).order_by('-rank', '-updated_at').distinct()
        else:
            # Fallback para SQLite
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(reference__icontains=value) |
                Q(messages__content__icontains=value)
            ).distinct()
```

## 3. Ejemplo de Template - Filtros

**Archivo:** `templates/tickets/ticket_list.html`

```html
<!-- Panel de Filtros Avanzados -->
<div class="bg-white rounded-2xl p-6 mb-8 shadow-lg">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold">
      <i class="fas fa-filter mr-2 text-blue-600"></i>
      Filtros Avanzados
    </h3>
    <button onclick="toggleFilters()">
      <i class="fas fa-chevron-down"></i>
      <span>Mostrar</span>
    </button>
  </div>

  <form method="get">
    <!-- Búsqueda -->
    <div>
      <label>🔍 Búsqueda</label>
      {{ filter.form.search }}
    </div>

    <!-- Estado -->
    <div>
      <label>🏁 Estado</label>
      <div class="space-y-2">
        {% for choice in filter.form.status %}
          <div class="flex items-center">
            {{ choice.tag }}
            <label for="{{ choice.id_for_label }}">
              {{ choice.choice_label }}
            </label>
          </div>
        {% endfor %}
      </div>
    </div>

    <!-- Prioridad -->
    <div>
      <label>⚠️ Prioridad</label>
      <div class="space-y-2">
        {% for choice in filter.form.priority %}
          <div class="flex items-center">
            {{ choice.tag }}
            <label for="{{ choice.id_for_label }}">
              {{ choice.choice_label }}
            </label>
          </div>
        {% endfor %}
      </div>
    </div>

    <!-- Botones -->
    <div class="flex gap-2">
      <button type="submit" class="btn-primary">
        <i class="fas fa-search"></i>
        Aplicar Filtros
      </button>
      <a href="{% url 'tickets:clear_filters' %}" class="btn-secondary">
        <i class="fas fa-times"></i>
        Limpiar
      </a>
    </div>
  </form>
</div>
```

## 4. Ejemplo de Template - Paginación

**Archivo:** `templates/tickets/ticket_list.html`

```html
<!-- Paginación -->
{% if is_paginated %}
<div class="flex justify-center mt-8">
  <nav class="bg-white rounded-xl p-2 shadow-lg">
    <div class="flex items-center space-x-1">
      <!-- Página Anterior -->
      {% if page_obj.has_previous %}
        <a href="?{% for key, value in request.GET.items %}
                   {% if key != 'page' %}{{ key }}={{ value }}&{% endif %}
                 {% endfor %}page={{ page_obj.previous_page_number }}" 
           class="px-3 py-2 rounded-lg hover:bg-gray-50">
          <i class="fas fa-chevron-left"></i>
        </a>
      {% endif %}
      
      <!-- Indicador de Página -->
      <span class="px-4 py-2 text-sm font-medium">
        Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
      </span>
      
      <!-- Página Siguiente -->
      {% if page_obj.has_next %}
        <a href="?{% for key, value in request.GET.items %}
                   {% if key != 'page' %}{{ key }}={{ value }}&{% endif %}
                 {% endfor %}page={{ page_obj.next_page_number }}" 
           class="px-3 py-2 rounded-lg hover:bg-gray-50">
          <i class="fas fa-chevron-right"></i>
        </a>
      {% endif %}
    </div>
  </nav>
</div>
{% endif %}
```

## 5. Ejemplo de Test

**Archivo:** `apps/tickets/tests.py`

```python
from django.test import TestCase, Client
from django.urls import reverse

class TicketFilterTestCase(TestCase):
    
    def setUp(self):
        # Crear datos de prueba
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            company=self.company,
            role='EMPLOYEE'
        )
        # Crear tickets con diferentes estados/prioridades
        self.ticket_high = Ticket.objects.create(
            reference='TKT-001',
            title='High Priority Ticket',
            status='OPEN',
            priority='HIGH',
            company=self.company,
            created_by=self.user
        )
    
    def test_filter_by_priority(self):
        """Test filtering tickets by priority"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('tickets:ticket_list') + '?priority=HIGH'
        )
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].priority, 'HIGH')
    
    def test_pagination_exists(self):
        """Test that pagination is present"""
        # Crear 25 tickets (más de 1 página)
        for i in range(25):
            Ticket.objects.create(
                reference=f'TKT-{i}',
                title=f'Ticket {i}',
                status='OPEN',
                priority='MEDIUM',
                company=self.company,
                created_by=self.user
            )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list'))
        
        # Verificar paginación
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['object_list']), 20)
```

## 6. URLs de Filtros

**Archivo:** `apps/tickets/urls.py`

```python
from django.urls import path
from .views import (
    TicketListView, save_filter, load_filter, 
    delete_filter, clear_filters
)

app_name = 'tickets'

urlpatterns = [
    # Lista de tickets con paginación y filtros
    path('', TicketListView.as_view(), name='ticket_list'),
    
    # Gestión de filtros guardados
    path('filters/save/', save_filter, name='save_filter'),
    path('filters/load/<int:filter_id>/', load_filter, name='load_filter'),
    path('filters/delete/<int:filter_id>/', delete_filter, name='delete_filter'),
    path('filters/clear/', clear_filters, name='clear_filters'),
]
```

## 7. Uso de la API

### Listar tickets (con paginación automática)
```
GET /tickets/
→ Retorna primera página (20 tickets)
```

### Navegar páginas
```
GET /tickets/?page=2
→ Retorna segunda página
```

### Filtrar por estado
```
GET /tickets/?status=OPEN
→ Solo tickets abiertos
```

### Filtrar por prioridad
```
GET /tickets/?priority=HIGH
→ Solo tickets de alta prioridad
```

### Búsqueda textual
```
GET /tickets/?search=problema+conexión
→ Busca "problema conexión" en título, descripción, etc.
```

### Combinación de filtros
```
GET /tickets/?status=OPEN&priority=HIGH&search=urgente
→ Tickets abiertos, alta prioridad, que contengan "urgente"
```

### Con paginación
```
GET /tickets/?status=OPEN&page=2
→ Segunda página de tickets abiertos
```

## 8. Estadísticas en Contexto

**Ejemplo de uso en template:**

```html
<!-- Panel de Estadísticas -->
<div class="grid grid-cols-6 gap-4">
  <div class="stat-card">
    <i class="fas fa-list text-blue-600"></i>
    <p>Total</p>
    <p class="text-2xl">{{ total_count }}</p>
  </div>
  
  <div class="stat-card">
    <i class="fas fa-folder-open text-green-600"></i>
    <p>Abiertos</p>
    <p class="text-2xl">{{ open_count }}</p>
  </div>
  
  <div class="stat-card">
    <i class="fas fa-spinner text-yellow-600"></i>
    <p>En Progreso</p>
    <p class="text-2xl">{{ in_progress_count }}</p>
  </div>
  
  <!-- ... más estadísticas ... -->
</div>
```

## 9. Ejecución de Tests

```bash
# Ejecutar todos los tests
python manage.py test apps.tickets.tests

# Ejecutar solo tests de paginación
python manage.py test apps.tickets.tests.TicketPaginationTestCase

# Ejecutar solo tests de filtros
python manage.py test apps.tickets.tests.TicketFilterTestCase

# Ejecutar test específico
python manage.py test apps.tickets.tests.TicketFilterTestCase.test_filter_by_priority

# Con verbosidad
python manage.py test apps.tickets.tests --verbosity=2
```

---

**Nota:** Todos estos ejemplos están extraídos del código real implementado en el proyecto.
