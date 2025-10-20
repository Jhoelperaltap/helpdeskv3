from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
from .models import EscalationRule, EscalationSettings, EscalationLog, Ticket
from .forms import EscalationRuleForm, EscalationSettingsForm
from apps.companies.models import Company
from django.contrib.auth import get_user_model
import socket

User = get_user_model()

class SuperAdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea SUPERADMIN"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'SUPERADMIN'
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard:dashboard')

class EscalationDashboardView(SuperAdminRequiredMixin, ListView):
    """Dashboard principal de administración de escalamiento"""
    template_name = 'tickets/admin/escalation_dashboard.html'
    context_object_name = 'escalation_logs'
    paginate_by = 20
    
    def get_queryset(self):
        return EscalationLog.objects.select_related(
            'ticket', 'escalation_rule', 'from_user', 'to_user', 'created_by'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        context.update({
            'total_escalations': EscalationLog.objects.filter(action='escalated').count(),
            'escalations_last_30_days': EscalationLog.objects.filter(
                action='escalated', 
                created_at__gte=last_30_days
            ).count(),
            'active_tickets_with_escalation': Ticket.objects.filter(
                status__in=['OPEN', 'IN_PROGRESS'],
                escalation_level__gt=0
            ).count(),
            'paused_escalations': Ticket.objects.filter(
                escalation_paused=True,
                status__in=['OPEN', 'IN_PROGRESS']
            ).count(),
            
            # Estadísticas por empresa
            'company_stats': self.get_company_escalation_stats(),
            
            # Próximos escalamientos
            'upcoming_escalations': Ticket.objects.filter(
                next_escalation_at__isnull=False,
                next_escalation_at__gte=now,
                next_escalation_at__lte=now + timedelta(hours=24),
                escalation_paused=False
            ).select_related('company', 'created_by', 'assigned_to')[:10],
            
            # Configuraciones activas
            'active_settings': EscalationSettings.objects.filter(enabled=True).count(),
            'active_rules': EscalationRule.objects.filter(is_active=True).count(),
        })
        
        return context
    
    def get_company_escalation_stats(self):
        """Obtiene estadísticas de escalamiento por empresa"""
        last_30_days = timezone.now() - timedelta(days=30)
        
        return Company.objects.annotate(
            total_escalations=Count(
                'tickets__escalation_logs',
                filter=Q(tickets__escalation_logs__action='escalated')
            ),
            recent_escalations=Count(
                'tickets__escalation_logs',
                filter=Q(
                    tickets__escalation_logs__action='escalated',
                    tickets__escalation_logs__created_at__gte=last_30_days
                )
            ),
            avg_escalation_level=Avg(
                'tickets__escalation_level',
                filter=Q(tickets__status__in=['OPEN', 'IN_PROGRESS'])
            )
        ).filter(total_escalations__gt=0).order_by('-recent_escalations')[:10]

class EscalationRuleListView(SuperAdminRequiredMixin, ListView):
    """Lista de reglas de escalamiento"""
    model = EscalationRule
    template_name = 'tickets/admin/escalation_rules.html'
    context_object_name = 'rules'
    paginate_by = 20
    
    def get_queryset(self):
        print("[v0] EscalationRuleListView: Iniciando get_queryset")
        
        queryset = EscalationRule.objects.select_related('company', 'escalate_to').order_by('company', 'priority', 'level')
        
        print(f"[v0] Total de reglas en BD: {queryset.count()}")
        
        # Filtros
        company_id = self.request.GET.get('company')
        priority = self.request.GET.get('priority')
        is_active = self.request.GET.get('is_active')
        
        print(f"[v0] Filtros aplicados - company: {company_id}, priority: {priority}, is_active: {is_active}")
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if priority:
            queryset = queryset.filter(priority=priority)
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        final_count = queryset.count()
        print(f"[v0] Reglas después de filtros: {final_count}")
        
        # Mostrar las reglas encontradas
        for rule in queryset:
            print(f"[v0] Regla encontrada: ID={rule.id}, Empresa={rule.company}, Prioridad={rule.priority}, Nivel={rule.level}")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        print("[v0] EscalationRuleListView: Iniciando get_context_data")
        
        context = super().get_context_data(**kwargs)
        
        print(f"[v0] Reglas en contexto: {len(context.get('rules', []))}")
        
        context.update({
            'companies': Company.objects.all(),
            'priorities': EscalationRule.PRIORITY_CHOICES,
            'current_filters': {
                'company': self.request.GET.get('company', ''),
                'priority': self.request.GET.get('priority', ''),
                'is_active': self.request.GET.get('is_active', ''),
            }
        })
        
        print(f"[v0] Empresas disponibles: {context['companies'].count()}")
        print(f"[v0] Prioridades disponibles: {len(context['priorities'])}")
        
        return context

class EscalationRuleCreateView(SuperAdminRequiredMixin, CreateView):
    """Crear nueva regla de escalamiento"""
    model = EscalationRule
    form_class = EscalationRuleForm
    template_name = 'tickets/admin/escalation_rule_form.html'
    success_url = reverse_lazy('tickets:admin_escalation_rules')
    
    def form_valid(self, form):
        messages.success(self.request, 'Regla de escalamiento creada exitosamente.')
        return super().form_valid(form)

class EscalationRuleUpdateView(SuperAdminRequiredMixin, UpdateView):
    """Editar regla de escalamiento"""
    model = EscalationRule
    form_class = EscalationRuleForm
    template_name = 'tickets/admin/escalation_rule_form.html'
    success_url = reverse_lazy('tickets:admin_escalation_rules')
    
    def form_valid(self, form):
        messages.success(self.request, 'Regla de escalamiento actualizada exitosamente.')
        return super().form_valid(form)

class EscalationRuleDeleteView(SuperAdminRequiredMixin, DeleteView):
    """Eliminar regla de escalamiento"""
    model = EscalationRule
    success_url = reverse_lazy('tickets:admin_escalation_rules')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Regla de escalamiento eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

class EscalationSettingsListView(SuperAdminRequiredMixin, ListView):
    """Lista de configuraciones de escalamiento"""
    model = EscalationSettings
    template_name = 'tickets/admin/escalation_settings.html'
    context_object_name = 'settings'
    
    def get_queryset(self):
        return EscalationSettings.objects.select_related('company').order_by('company__name')

class EscalationSettingsCreateView(SuperAdminRequiredMixin, CreateView):
    """Crear nueva configuración de escalamiento"""
    model = EscalationSettings
    form_class = EscalationSettingsForm
    template_name = 'tickets/admin/escalation_settings_form.html'
    success_url = reverse_lazy('tickets:admin_escalation_settings')
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración de escalamiento creada exitosamente.')
        return super().form_valid(form)

class EscalationSettingsUpdateView(SuperAdminRequiredMixin, UpdateView):
    """Editar configuración de escalamiento"""
    model = EscalationSettings
    form_class = EscalationSettingsForm
    template_name = 'tickets/admin/escalation_settings_form.html'
    success_url = reverse_lazy('tickets:admin_escalation_settings')
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración de escalamiento actualizada exitosamente.')
        return super().form_valid(form)

class EscalationLogDetailView(SuperAdminRequiredMixin, DetailView):
    """Detalle de un log de escalamiento"""
    model = EscalationLog
    template_name = 'tickets/admin/escalation_log_detail.html'
    context_object_name = 'log'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log = self.object
        
        # Obtener logs relacionados del mismo ticket
        context['related_logs'] = EscalationLog.objects.filter(
            ticket=log.ticket
        ).exclude(id=log.id).order_by('-created_at')[:10]
        
        return context

class EscalationReportView(SuperAdminRequiredMixin, ListView):
    """Vista de reportes de escalamiento"""
    template_name = 'tickets/admin/escalation_reports.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        # Filtros de fecha
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        company_id = self.request.GET.get('company')
        action = self.request.GET.get('action')
        
        queryset = EscalationLog.objects.select_related(
            'ticket', 'escalation_rule', 'from_user', 'to_user'
        ).order_by('-created_at')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if company_id:
            queryset = queryset.filter(ticket__company_id=company_id)
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del período filtrado
        queryset = self.get_queryset()
        
        context.update({
            'companies': Company.objects.all(),
            'actions': EscalationLog.ACTION_CHOICES,
            'current_filters': {
                'date_from': self.request.GET.get('date_from', ''),
                'date_to': self.request.GET.get('date_to', ''),
                'company': self.request.GET.get('company', ''),
                'action': self.request.GET.get('action', ''),
            },
            'total_logs': queryset.count(),
            'escalations_count': queryset.filter(action='escalated').count(),
            'paused_count': queryset.filter(action='paused').count(),
            'resumed_count': queryset.filter(action='resumed').count(),
        })
        
        return context

def escalation_stats_api(request):
    """API para obtener estadísticas de escalamiento en tiempo real"""
    if not request.user.is_authenticated or request.user.role != 'SUPERADMIN':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    stats = {
        'escalations_24h': EscalationLog.objects.filter(
            action='escalated',
            created_at__gte=last_24h
        ).count(),
        'escalations_7d': EscalationLog.objects.filter(
            action='escalated',
            created_at__gte=last_7d
        ).count(),
        'escalations_30d': EscalationLog.objects.filter(
            action='escalated',
            created_at__gte=last_30d
        ).count(),
        'active_escalated_tickets': Ticket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS'],
            escalation_level__gt=0
        ).count(),
        'upcoming_escalations': Ticket.objects.filter(
            next_escalation_at__isnull=False,
            next_escalation_at__gte=now,
            next_escalation_at__lte=now + timedelta(hours=24),
            escalation_paused=False
        ).count(),
        'paused_escalations': Ticket.objects.filter(
            escalation_paused=True,
            status__in=['OPEN', 'IN_PROGRESS']
        ).count(),
    }
    
    return JsonResponse(stats)

def toggle_escalation_rule(request, pk):
    """Activar/desactivar regla de escalamiento"""
    if not request.user.is_authenticated or request.user.role != 'SUPERADMIN':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        rule = get_object_or_404(EscalationRule, pk=pk)
        rule.is_active = not rule.is_active
        rule.save()
        
        action = 'activada' if rule.is_active else 'desactivada'
        messages.success(request, f'Regla de escalamiento {action} exitosamente.')
        
        return JsonResponse({
            'success': True,
            'is_active': rule.is_active,
            'message': f'Regla {action}'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def bulk_escalation_actions(request):
    """Acciones masivas sobre escalamientos"""
    if not request.user.is_authenticated or request.user.role != 'SUPERADMIN':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        ticket_ids = request.POST.getlist('ticket_ids')
        
        if not action or not ticket_ids:
            return JsonResponse({'error': 'Acción o tickets no especificados'}, status=400)
        
        tickets = Ticket.objects.filter(id__in=ticket_ids)
        count = 0
        
        if action == 'pause_escalation':
            tickets.update(escalation_paused=True)
            count = tickets.count()
            messages.success(request, f'Escalamiento pausado para {count} tickets.')
            
        elif action == 'resume_escalation':
            tickets.update(escalation_paused=False)
            count = tickets.count()
            messages.success(request, f'Escalamiento reanudado para {count} tickets.')
            
        elif action == 'reset_escalation':
            tickets.update(escalation_level=0, escalation_paused=False, next_escalation_at=None)
            count = tickets.count()
            messages.success(request, f'Escalamiento reiniciado para {count} tickets.')
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'Acción aplicada a {count} tickets'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

class EmailTestView(SuperAdminRequiredMixin, ListView):
    """Vista para probar el sistema de emails en desarrollo"""
    template_name = 'tickets/admin/email_test.html'
    context_object_name = 'test_results'
    
    def get_queryset(self):
        return []  # No necesitamos queryset para esta vista
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.conf import settings
        import os
        
        smtp_connection_status = self.test_smtp_connection_fast()
        
        # Verificar configuración actual de Django
        email_user_configured = bool(settings.EMAIL_HOST_USER)
        email_password_configured = bool(settings.EMAIL_HOST_PASSWORD)
        is_smtp_backend = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        
        # Verificar variables de entorno directamente
        env_email_backend = os.environ.get('EMAIL_BACKEND', '')
        env_email_host = os.environ.get('EMAIL_HOST', '')
        env_email_user = os.environ.get('EMAIL_HOST_USER', '')
        env_email_password = bool(os.environ.get('EMAIL_HOST_PASSWORD', ''))
        
        # Detectar discrepancias entre .env y Django
        config_mismatch = (
            env_email_backend != settings.EMAIL_BACKEND or
            env_email_host != settings.EMAIL_HOST or
            env_email_user != settings.EMAIL_HOST_USER
        )
        
        context.update({
            # Configuración actual de Django
            'email_backend': settings.EMAIL_BACKEND,
            'email_host': settings.EMAIL_HOST,
            'email_port': settings.EMAIL_PORT,
            'email_use_tls': settings.EMAIL_USE_TLS,
            'email_host_user': settings.EMAIL_HOST_USER,
            'email_user_configured': email_user_configured,
            'email_password_configured': email_password_configured,
            'is_smtp_backend': is_smtp_backend,
            'default_from_email': settings.DEFAULT_FROM_EMAIL,
            'admin_email': getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'notifications_enabled': getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', True),
            
            # Variables de entorno para comparación
            'env_email_backend': env_email_backend,
            'env_email_host': env_email_host,
            'env_email_user': env_email_user,
            'env_email_password_set': env_email_password,
            'config_mismatch': config_mismatch,
            
            'smtp_connection_status': smtp_connection_status,
            'smtp_connection_success': smtp_connection_status.get('success', False),
            'smtp_connection_error': smtp_connection_status.get('error', ''),
            
            # Datos para pruebas
            'users_for_testing': User.objects.filter(is_active=True)[:10],
            'recent_tickets': Ticket.objects.select_related('company', 'created_by')[:5],
            
            # Estado de configuración
            'smtp_ready': is_smtp_backend and email_user_configured and email_password_configured and smtp_connection_status.get('success', False),
            'needs_restart': config_mismatch,
        })
        
        return context
    
    def test_smtp_connection_fast(self):
        """
        Prueba rápida de conexión SMTP con timeout corto para evitar 504 en producción
        """
        import socket
        import os
        
        try:
            host = os.environ.get('EMAIL_HOST', '')
            port = int(os.environ.get('EMAIL_PORT', 587))
            username = os.environ.get('EMAIL_HOST_USER', '')
            password = os.environ.get('EMAIL_HOST_PASSWORD', '')
            
            if not username or not password:
                return {
                    'success': False,
                    'error': 'Configuración SMTP incompleta',
                    'details': {'host': host, 'port': port, 'username': username}
                }
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            
            try:
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    return {
                        'success': True,
                        'message': f'Puerto SMTP {port} accesible en {host}',
                        'details': {'host': host, 'port': port, 'username': username}
                    }
                else:
                    return {
                        'success': False,
                        'error': f'No se puede conectar al puerto {port}',
                        'suggestions': ['Verifica firewall', 'Verifica host y puerto']
                    }
            except socket.timeout:
                return {
                    'success': False,
                    'error': 'Timeout conectando a SMTP (3s)',
                    'suggestions': ['Verifica conexión a internet', 'Verifica firewall']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestions': ['Verifica configuración en .env']
            }

    def post(self, request, *args, **kwargs):
        """Manejar envío de emails con timeouts cortos"""
        from django.core.mail import send_mail, EmailMessage, get_connection
        from django.conf import settings
        import os
        
        test_type = request.POST.get('test_type')
        recipient_email = request.POST.get('recipient_email', 'test@example.com')
        
        try:
            smtp_connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=os.environ.get('EMAIL_HOST', settings.EMAIL_HOST),
                port=int(os.environ.get('EMAIL_PORT', settings.EMAIL_PORT)),
                username=os.environ.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
                password=os.environ.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD),
                use_tls=os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true',
                timeout=10,  # Timeout de 10 segundos
            )
        except Exception as e:
            messages.error(request, f'Error creando conexión SMTP: {str(e)}')
            return redirect('tickets:admin_email_test')
        
        if not smtp_connection.username or not smtp_connection.password:
            messages.error(request, 'Configuración SMTP incompleta')
            return redirect('tickets:admin_email_test')
        
        try:
            if test_type == 'connection':
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((smtp_connection.host, smtp_connection.port))
                sock.close()
                
                if result == 0:
                    messages.success(request, f'Conexión SMTP exitosa a {smtp_connection.host}:{smtp_connection.port}')
                else:
                    messages.error(request, f'No se puede conectar al puerto {smtp_connection.port}')
                return redirect('tickets:admin_email_test')
            
            if test_type == 'basic':
                send_mail(
                    subject='[Helpdesk] Prueba Básica SMTP',
                    message=f'Email de prueba desde {smtp_connection.host}',
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    recipient_list=[recipient_email],
                    connection=smtp_connection,
                    fail_silently=False,
                )
                messages.success(request, f'Email enviado a {recipient_email}')
                
            elif test_type == 'html':
                html_content = f"""
                <html><body>
                <h1>Prueba HTML SMTP</h1>
                <p>Configuración: {smtp_connection.host}:{smtp_connection.port}</p>
                <p>Usuario: {smtp_connection.username}</p>
                </body></html>
                """
                
                email = EmailMessage(
                    subject='[Helpdesk] Prueba HTML SMTP',
                    body=html_content,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    to=[recipient_email],
                    connection=smtp_connection,
                )
                email.content_subtype = 'html'
                email.send()
                messages.success(request, f'Email HTML enviado a {recipient_email}')
                
        except socket.timeout:
            messages.error(request, 'Timeout enviando email. Verifica configuración SMTP.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('tickets:admin_email_test')
