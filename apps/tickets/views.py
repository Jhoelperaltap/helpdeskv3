from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from .models import Ticket, TicketMessage, TicketAttachment, SavedFilter, EscalationLog
from .filters import TicketFilter
from apps.notifications.utils import notify_ticket_created, notify_ticket_updated, notify_ticket_resolved, notify_message_added
from .tasks import resume_escalation, pause_escalation_on_response
from django import forms
import uuid
import json

class TicketForm(forms.ModelForm):
    attachment = forms.FileField(required=False)
    
    class Meta:
        model = Ticket
        fields = ['title','description','priority']

def generate_reference():
    return 'TKT-' + uuid.uuid4().hex[:8].upper()

class TicketListView(LoginRequiredMixin, FilterView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    login_url = '/users/login/'
    filterset_class = TicketFilter
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('company','created_by','assigned_to')
        
        if user.is_superadmin():
            # SUPERADMIN: Ve todos los tickets de todas las empresas
            base_qs = qs
        elif user.is_technician():
            # TECHNICIAN: Ve todos los tickets (para dar soporte)
            base_qs = qs
        elif user.is_company_admin():
            # COMPANY_ADMIN: Ve solo tickets de su empresa
            base_qs = qs.filter(company=user.company)
        else:  # EMPLOYEE
            # EMPLOYEE: Ve solo sus propios tickets
            base_qs = qs.filter(created_by=user)
        
        return base_qs.order_by('-updated_at')
    
    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['request'] = self.request
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar estadísticas
        queryset = self.get_queryset()
        context['total_count'] = queryset.count()
        context['open_count'] = queryset.filter(status='OPEN').count()
        context['in_progress_count'] = queryset.filter(status='IN_PROGRESS').count()
        context['resolved_count'] = queryset.filter(status='RESOLVED').count()
        context['closed_count'] = queryset.filter(status='CLOSED').count()
        context['high_priority_count'] = queryset.filter(priority='HIGH').count()
        
        # Agregar filtros guardados del usuario
        context['saved_filters'] = SavedFilter.objects.filter(user=self.request.user)
        
        # Verificar si hay filtros activos
        context['has_active_filters'] = bool(self.request.GET.dict())
        
        return context

@login_required
@require_POST
def save_filter(request):
    """Guardar filtro actual como filtro guardado"""
    filter_name = request.POST.get('filter_name', '').strip()
    is_default = request.POST.get('is_default') == 'on'
    
    if not filter_name:
        messages.error(request, 'Debes proporcionar un nombre para el filtro.')
        return redirect('tickets:ticket_list')
    
    # Obtener parámetros de filtro actuales (excluyendo page y filter_name)
    filter_params = request.GET.dict()
    filter_params.pop('page', None)
    
    if not filter_params:
        messages.error(request, 'No hay filtros activos para guardar.')
        return redirect('tickets:ticket_list')
    
    try:
        # Crear o actualizar filtro guardado
        saved_filter, created = SavedFilter.objects.update_or_create(
            user=request.user,
            name=filter_name,
            defaults={
                'filter_data': filter_params,
                'is_default': is_default
            }
        )
        
        action = 'creado' if created else 'actualizado'
        messages.success(request, f'Filtro "{filter_name}" {action} exitosamente.')
        
    except Exception as e:
        messages.error(request, f'Error al guardar el filtro: {str(e)}')
    
    return redirect('tickets:ticket_list')

@login_required
def load_filter(request, filter_id):
    """Cargar un filtro guardado"""
    try:
        saved_filter = get_object_or_404(SavedFilter, id=filter_id, user=request.user)
        filter_params = saved_filter.get_filter_params()
        
        # Construir URL con parámetros del filtro
        query_string = '&'.join([f'{k}={v}' for k, v in filter_params.items() if v])
        redirect_url = f"{request.build_absolute_uri('/tickets/')}?{query_string}"
        
        messages.success(request, f'Filtro "{saved_filter.name}" aplicado.')
        return redirect(redirect_url)
        
    except SavedFilter.DoesNotExist:
        messages.error(request, 'Filtro no encontrado.')
        return redirect('tickets:ticket_list')

@login_required
@require_POST
def delete_filter(request, filter_id):
    """Eliminar un filtro guardado"""
    try:
        saved_filter = get_object_or_404(SavedFilter, id=filter_id, user=request.user)
        filter_name = saved_filter.name
        saved_filter.delete()
        
        messages.success(request, f'Filtro "{filter_name}" eliminado exitosamente.')
        
    except SavedFilter.DoesNotExist:
        messages.error(request, 'Filtro no encontrado.')
    
    return redirect('tickets:ticket_list')

@login_required
def clear_filters(request):
    """Limpiar todos los filtros activos"""
    messages.info(request, 'Filtros limpiados.')
    return redirect('tickets:ticket_list')

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    login_url = '/users/login/'
    
    def get_object(self, queryset=None):
        ticket = get_object_or_404(Ticket, pk=self.kwargs['pk'])
        user = self.request.user
        
        # Check if user has permission to view this ticket
        if user.is_superadmin() or user.is_technician():
            # SUPERADMIN and TECHNICIAN can see all tickets
            pass
        elif user.is_company_admin():
            # COMPANY_ADMIN can only see tickets from their company
            if ticket.company != user.company:
                raise PermissionDenied("No tienes permisos para ver este ticket.")
        else:  # EMPLOYEE
            # EMPLOYEE can only see their own tickets
            if ticket.created_by != user:
                raise PermissionDenied("No tienes permisos para ver este ticket.")
        
        return ticket
    
    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        content = request.POST.get('content')
        file = request.FILES.get('attachment')
        
        if content:
            private = False
            if request.user.is_technician() or request.user.is_superadmin():
                private = request.POST.get('private') == 'true'
            
            msg = TicketMessage.objects.create(
                ticket=ticket, 
                sender=request.user, 
                content=content,
                private=private
            )
            
            if file:
                TicketAttachment.objects.create(ticket=ticket, message=msg, file=file)
            
            if not private:  # Solo para mensajes públicos
                ticket.last_response_at = timezone.now()
                ticket.save()
            
            notify_message_added(ticket, msg, request.user)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': msg.id,
                        'content': msg.content,
                        'sender': msg.sender.get_full_name() or msg.sender.username,
                        'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M'),
                        'private': msg.private,
                        'is_staff': msg.sender.is_technician() or msg.sender.is_superadmin()
                    }
                })
            
            messages.success(request, 'Mensaje agregado exitosamente.')
        
        return redirect(ticket.get_absolute_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_send_private'] = self.request.user.is_technician() or self.request.user.is_superadmin()
        
        ticket = self.object
        context['escalation_logs'] = EscalationLog.objects.filter(ticket=ticket).order_by('-created_at')[:10]
        context['can_manage_escalation'] = self.request.user.is_technician() or self.request.user.is_superadmin()
        
        return context

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_create.html'
    login_url = '/users/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Only users with companies can create tickets (except superadmin/technician)
        if not request.user.is_superadmin() and not request.user.is_technician():
            if not request.user.company:
                messages.error(request, 'Debes tener una empresa asignada para crear tickets.')
                return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        t = form.save(commit=False)
        t.created_by = self.request.user
        
        if self.request.user.is_superadmin() or self.request.user.is_technician():
            # For superadmin/technician, they might not have a company but can create tickets
            # In this case, we might want to add a company field to the form or handle differently
            if not self.request.user.company:
                messages.error(self.request, 'Los técnicos y superadmin deben especificar una empresa para el ticket.')
                return self.form_invalid(form)
        
        t.company = self.request.user.company
        t.reference = generate_reference()
        t.save()
        
        file = form.cleaned_data.get('attachment')
        if file:
            msg = TicketMessage.objects.create(ticket=t, sender=self.request.user, content='Adjunto cargado')
            TicketAttachment.objects.create(ticket=t, message=msg, file=file)
        
        notify_ticket_created(t, self.request.user)
        
        messages.success(self.request, f'Ticket {t.reference} creado exitosamente.')
        return redirect(t.get_absolute_url())

class TicketEditView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_edit.html'
    login_url = '/users/login/'
    
    def get_object(self, queryset=None):
        ticket = get_object_or_404(Ticket, pk=self.kwargs['pk'])
        user = self.request.user
        
        # Check if user has permission to edit this ticket
        if user.is_superadmin() or user.is_technician():
            # SUPERADMIN and TECHNICIAN can edit all tickets
            pass
        elif user.is_company_admin():
            # COMPANY_ADMIN can only edit tickets from their company
            if ticket.company != user.company:
                raise PermissionDenied("No tienes permisos para editar este ticket.")
        else:  # EMPLOYEE
            # EMPLOYEE can only edit their own tickets if they're still open
            if ticket.created_by != user:
                raise PermissionDenied("No tienes permisos para editar este ticket.")
            if ticket.status in ['CLOSED', 'RESOLVED']:
                raise PermissionDenied("No puedes editar un ticket cerrado o resuelto.")
        
        return ticket
    
    def form_valid(self, form):
        notify_ticket_updated(self.object, self.request.user)
        
        messages.success(self.request, f'Ticket {self.object.reference} actualizado exitosamente.')
        return super().form_valid(form)

@login_required
@require_POST
def ticket_close(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    
    # Only technicians and superadmins can close tickets
    if not (user.is_technician() or user.is_superadmin()):
        raise PermissionDenied("No tienes permisos para cerrar tickets.")
    
    close_as_resolved = request.POST.get('resolved') == 'true'
    
    if ticket.status not in ['CLOSED', 'RESOLVED']:
        if close_as_resolved:
            ticket.status = 'RESOLVED'
            status_text = "resuelto"
        else:
            ticket.status = 'CLOSED'
            status_text = "cerrado"
        
        ticket.escalation_paused = True
        ticket.next_escalation_at = None
        ticket.save()
        
        # Add a system message
        TicketMessage.objects.create(
            ticket=ticket,
            sender=user,
            content=f"Ticket {status_text} por {user.get_full_name() or user.username}",
            private=True
        )
        
        if close_as_resolved:
            notify_ticket_resolved(ticket, user)
        else:
            notify_ticket_updated(ticket, user)
        
        messages.success(request, f'Ticket {ticket.reference} {status_text} exitosamente.')
    else:
        messages.info(request, 'El ticket ya estaba cerrado o resuelto.')
    
    return redirect(ticket.get_absolute_url())

@login_required
@require_POST
def ticket_reopen(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    
    # Only technicians and superadmins can reopen tickets
    if not (user.is_technician() or user.is_superadmin()):
        raise PermissionDenied("No tienes permisos para reabrir tickets.")
    
    if ticket.status == 'CLOSED':
        ticket.status = 'OPEN'
        ticket.escalation_paused = False
        ticket.last_response_at = timezone.now()
        ticket.save()
        
        # Add a system message
        TicketMessage.objects.create(
            ticket=ticket,
            sender=user,
            content=f"Ticket reabierto por {user.get_full_name() or user.username}",
            private=True
        )
        
        resume_escalation.delay(ticket.id)
        
        messages.success(request, f'Ticket {ticket.reference} reabierto exitosamente.')
    else:
        messages.info(request, 'El ticket no estaba cerrado.')
    
    return redirect(ticket.get_absolute_url())

@login_required
@require_POST
def pause_escalation(request, pk):
    """Pausar escalamiento manualmente"""
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    
    # Solo técnicos y superadmins pueden pausar escalamiento
    if not (user.is_technician() or user.is_superadmin()):
        raise PermissionDenied("No tienes permisos para pausar escalamiento.")
    
    if not ticket.escalation_paused:
        ticket.escalation_paused = True
        ticket.save()
        
        # Registrar la acción
        EscalationLog.objects.create(
            ticket=ticket,
            action='paused',
            level=ticket.escalation_level,
            notes="Escalamiento pausado manualmente",
            created_by=user
        )
        
        messages.success(request, f'Escalamiento pausado para ticket {ticket.reference}.')
    else:
        messages.info(request, 'El escalamiento ya estaba pausado.')
    
    return redirect(ticket.get_absolute_url())

@login_required
@require_POST
def resume_escalation_view(request, pk):
    """Reanudar escalamiento manualmente"""
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    
    # Solo técnicos y superadmins pueden reanudar escalamiento
    if not (user.is_technician() or user.is_superadmin()):
        raise PermissionDenied("No tienes permisos para reanudar escalamiento.")
    
    if ticket.escalation_paused:
        # Ejecutar tarea asíncrona para reanudar
        resume_escalation.delay(ticket.id)
        
        messages.success(request, f'Escalamiento reanudado para ticket {ticket.reference}.')
    else:
        messages.info(request, 'El escalamiento no estaba pausado.')
    
    return redirect(ticket.get_absolute_url())

@login_required
def escalation_history(request, pk):
    """Ver historial completo de escalamiento de un ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    
    # Verificar permisos
    if user.is_superadmin() or user.is_technician():
        pass
    elif user.is_company_admin():
        if ticket.company != user.company:
            raise PermissionDenied("No tienes permisos para ver este ticket.")
    else:
        if ticket.created_by != user:
            raise PermissionDenied("No tienes permisos para ver este ticket.")
    
    escalation_logs = EscalationLog.objects.filter(ticket=ticket).order_by('-created_at')
    
    return JsonResponse({
        'ticket_reference': ticket.reference,
        'escalation_level': ticket.escalation_level,
        'escalation_paused': ticket.escalation_paused,
        'next_escalation_at': ticket.next_escalation_at.isoformat() if ticket.next_escalation_at else None,
        'logs': [
            {
                'action': log.get_action_display(),
                'level': log.level,
                'from_user': log.from_user.username if log.from_user else None,
                'to_user': log.to_user.username if log.to_user else None,
                'notes': log.notes,
                'created_at': log.created_at.strftime('%d/%m/%Y %H:%M'),
                'created_by': log.created_by.username if log.created_by else 'Sistema'
            }
            for log in escalation_logs
        ]
    })
