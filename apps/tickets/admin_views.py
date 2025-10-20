from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
from .models import EscalationRule, EscalationSettings, EscalationLog, Ticket, EmailLog
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
    context_object_name = 'email_logs'
    paginate_by = 10
    
    def get_queryset(self):
        return EmailLog.objects.filter(sent_by=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.conf import settings
        import os
        
        smtp_connection_status = self.test_smtp_connection_fast()
        
        email_user_configured = bool(settings.EMAIL_HOST_USER)
        email_password_configured = bool(settings.EMAIL_HOST_PASSWORD)
        is_smtp_backend = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        
        env_email_backend = os.environ.get('EMAIL_BACKEND', '')
        env_email_host = os.environ.get('EMAIL_HOST', '')
        env_email_user = os.environ.get('EMAIL_HOST_USER', '')
        env_email_password = bool(os.environ.get('EMAIL_HOST_PASSWORD', ''))
        
        config_mismatch = (
            env_email_backend != settings.EMAIL_BACKEND or
            env_email_host != settings.EMAIL_HOST or
            env_email_user != settings.EMAIL_HOST_USER
        )
        
        context.update({
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
            
            'env_email_backend': env_email_backend,
            'env_email_host': env_email_host,
            'env_email_user': env_email_user,
            'env_email_password_set': env_email_password,
            'config_mismatch': config_mismatch,
            
            'smtp_connection_status': smtp_connection_status,
            'smtp_connection_success': smtp_connection_status.get('success', False),
            'smtp_connection_error': smtp_connection_status.get('error', ''),
            
            'users_for_testing': User.objects.filter(is_active=True)[:10],
            'recent_tickets': Ticket.objects.select_related('company', 'created_by')[:5],
            
            'smtp_ready': is_smtp_backend and email_user_configured and email_password_configured and smtp_connection_status.get('success', False),
            'needs_restart': config_mismatch,
            
            'total_sent': EmailLog.objects.filter(sent_by=self.request.user, status='sent').count(),
            'total_failed': EmailLog.objects.filter(sent_by=self.request.user, status='failed').count(),
            'total_pending': EmailLog.objects.filter(sent_by=self.request.user, status__in=['pending', 'sending']).count(),
        })
        
        return context
    
    def test_smtp_connection_fast(self):
        """Prueba rápida de conexión SMTP con timeout corto para evitar 504 en producción"""
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

    def send_email_async(self, email_log_id, email_func):
        """Envía email en un thread separado y actualiza el log"""
        import threading
        from django.utils import timezone
        
        def send_in_background():
            try:
                email_log = EmailLog.objects.get(id=email_log_id)
                email_log.status = 'sending'
                email_log.save()
                
                # Ejecutar función de envío
                email_func()
                
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save()
                
                print(f"[v0] Email enviado exitosamente: {email_log.email_type} a {email_log.recipient}")
                
            except Exception as e:
                try:
                    email_log = EmailLog.objects.get(id=email_log_id)
                    email_log.status = 'failed'
                    email_log.error_message = str(e)
                    email_log.save()
                except:
                    pass
                
                print(f"[v0] Error enviando email: {str(e)}")
        
        thread = threading.Thread(target=send_in_background)
        thread.daemon = True
        thread.start()

    def post(self, request, *args, **kwargs):
        """Manejar envío de emails con logging completo"""
        from django.core.mail import send_mail, EmailMessage, get_connection
        from django.conf import settings
        import os
        
        test_type = request.POST.get('test_type')
        recipient_email = request.POST.get('recipient_email', 'test@example.com')
        
        if not recipient_email or '@' not in recipient_email:
            messages.error(request, 'Email de destino inválido')
            return redirect('tickets:admin_email_test')
        
        try:
            email_port = int(os.environ.get('EMAIL_PORT', settings.EMAIL_PORT))
            
            # Puerto 465 usa SSL, puerto 587 usa TLS
            use_ssl = email_port == 465
            use_tls = email_port == 587
            
            smtp_connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=os.environ.get('EMAIL_HOST', settings.EMAIL_HOST),
                port=email_port,
                username=os.environ.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
                password=os.environ.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD),
                use_ssl=use_ssl,  # SSL para puerto 465
                use_tls=use_tls,  # TLS para puerto 587
                timeout=60,  # Aumentado a 60 segundos para producción
            )
        except Exception as e:
            messages.error(request, f'Error creando conexión SMTP: {str(e)}')
            return redirect('tickets:admin_email_test')
        
        if not smtp_connection.username or not smtp_connection.password:
            messages.error(request, 'Configuración SMTP incompleta. Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en .env')
            return redirect('tickets:admin_email_test')
        
        try:
            if test_type == 'connection':
                email_log = EmailLog.objects.create(
                    email_type='connection_test',
                    recipient=recipient_email,
                    subject='Prueba de Conexión SMTP',
                    smtp_host=smtp_connection.host,
                    smtp_port=smtp_connection.port,
                    sent_by=request.user,
                    status='pending'
                )
                
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # Timeout más largo para prueba de conexión
                result = sock.connect_ex((smtp_connection.host, smtp_connection.port))
                sock.close()
                
                if result == 0:
                    email_log.status = 'sent'
                    email_log.sent_at = timezone.now()
                    email_log.save()
                    messages.success(request, f'Conexión SMTP exitosa a {smtp_connection.host}:{smtp_connection.port}')
                else:
                    email_log.status = 'failed'
                    email_log.error_message = f'No se puede conectar al puerto {smtp_connection.port}'
                    email_log.save()
                    messages.error(request, f'No se puede conectar al puerto {smtp_connection.port}. Verifica firewall y configuración.')
                return redirect('tickets:admin_email_test')
            
            from_email = os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
            
            if test_type == 'basic':
                email_log = EmailLog.objects.create(
                    email_type='basic',
                    recipient=recipient_email,
                    subject='[Helpdesk] Prueba Básica SMTP',
                    smtp_host=smtp_connection.host,
                    smtp_port=smtp_connection.port,
                    sent_by=request.user,
                    status='pending'
                )
                
                def send_basic_email():
                    send_mail(
                        subject='[Helpdesk] Prueba Básica SMTP',
                        message=f'Este es un email de prueba enviado desde el sistema Helpdesk.\n\nConfiguración SMTP:\n- Host: {smtp_connection.host}\n- Puerto: {smtp_connection.port}\n- Usuario: {smtp_connection.username}\n- SSL: {"Activado" if use_ssl else "Desactivado"}\n- TLS: {"Activado" if use_tls else "Desactivado"}\n\nSi recibes este email, la configuración SMTP está funcionando correctamente.',
                        from_email=from_email,
                        recipient_list=[recipient_email],
                        connection=smtp_connection,
                        fail_silently=False,
                    )
                
                self.send_email_async(email_log.id, send_basic_email)
                messages.success(request, f'Email básico en proceso de envío a {recipient_email}. Revisa el estado abajo en unos segundos.')
                
            elif test_type == 'html':
                email_log = EmailLog.objects.create(
                    email_type='html',
                    recipient=recipient_email,
                    subject='[Helpdesk] Prueba HTML SMTP',
                    smtp_host=smtp_connection.host,
                    smtp_port=smtp_connection.port,
                    sent_by=request.user,
                    status='pending'
                )
                
                def send_html_email():
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                            .info-box {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4F46E5; }}
                            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Prueba HTML SMTP</h1>
                            </div>
                            <div class="content">
                                <p>Este es un email de prueba con formato HTML enviado desde el sistema Helpdesk.</p>
                                
                                <div class="info-box">
                                    <h3>Configuración SMTP</h3>
                                    <p><strong>Host:</strong> {smtp_connection.host}</p>
                                    <p><strong>Puerto:</strong> {smtp_connection.port}</p>
                                    <p><strong>Usuario:</strong> {smtp_connection.username}</p>
                                    <p><strong>TLS:</strong> {'Activado' if smtp_connection.use_tls else 'Desactivado'}</p>
                                </div>
                                
                                <p>Si recibes este email con el formato correcto, tu configuración SMTP está funcionando perfectamente.</p>
                            </div>
                            <div class="footer">
                                <p>Sistema Helpdesk - Prueba de Email</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    email = EmailMessage(
                        subject='[Helpdesk] Prueba HTML SMTP',
                        body=html_content,
                        from_email=from_email,
                        to=[recipient_email],
                        connection=smtp_connection,
                    )
                    email.content_subtype = 'html'
                    email.send()
                
                self.send_email_async(email_log.id, send_html_email)
                messages.success(request, f'Email HTML en proceso de envío a {recipient_email}. Revisa el estado abajo.')
            
            elif test_type == 'ticket_notification':
                email_log = EmailLog.objects.create(
                    email_type='ticket_notification',
                    recipient=recipient_email,
                    subject='[Helpdesk] Nuevo Ticket #TEST-001',
                    smtp_host=smtp_connection.host,
                    smtp_port=smtp_connection.port,
                    sent_by=request.user,
                    status='pending'
                )
                
                def send_ticket_notification():
                    html_content = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                            .header { background: #EF4444; color: white; padding: 20px; text-align: center; }
                            .ticket-info { background: #f9fafb; padding: 20px; margin: 20px 0; }
                            .ticket-info p { margin: 10px 0; }
                            .button { display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Nuevo Ticket Creado</h1>
                            </div>
                            <div class="ticket-info">
                                <p><strong>Ticket #:</strong> TEST-001</p>
                                <p><strong>Asunto:</strong> Prueba de notificación de ticket</p>
                                <p><strong>Prioridad:</strong> Alta</p>
                                <p><strong>Estado:</strong> Abierto</p>
                                <p><strong>Creado por:</strong> Sistema de Pruebas</p>
                            </div>
                            <p>Este es un ejemplo de cómo se verán las notificaciones automáticas de tickets.</p>
                            <a href="#" class="button">Ver Ticket</a>
                        </div>
                    </body>
                    </html>
                    """
                    
                    email = EmailMessage(
                        subject='[Helpdesk] Nuevo Ticket #TEST-001',
                        body=html_content,
                        from_email=from_email,
                        to=[recipient_email],
                        connection=smtp_connection,
                    )
                    email.content_subtype = 'html'
                    email.send()
                
                self.send_email_async(email_log.id, send_ticket_notification)
                messages.success(request, f'Notificación de ticket en proceso de envío a {recipient_email}. Revisa el estado abajo.')
            
            elif test_type == 'bulk':
                test_users = User.objects.filter(is_active=True, role='SUPERADMIN')[:3]
                
                for user in test_users:
                    email_log = EmailLog.objects.create(
                        email_type='bulk',
                        recipient=user.email,
                        subject='[Helpdesk] Prueba de Envío Masivo',
                        smtp_host=smtp_connection.host,
                        smtp_port=smtp_connection.port,
                        sent_by=request.user,
                        status='pending'
                    )
                    
                    def send_bulk_email(user_obj=user, log_id=email_log.id):
                        send_mail(
                            subject='[Helpdesk] Prueba de Envío Masivo',
                            message=f'Hola {user_obj.get_full_name()},\n\nEste es un email de prueba masiva del sistema Helpdesk.',
                            from_email=from_email,
                            recipient_list=[user_obj.email],
                            connection=smtp_connection,
                            fail_silently=False,
                        )
                    
                    self.send_email_async(email_log.id, send_bulk_email)
                
                messages.success(request, f'Envío masivo en proceso a {test_users.count()} usuarios. Revisa el estado abajo.')
            
            else:
                messages.error(request, 'Tipo de prueba no válido')
                
        except socket.timeout:
            messages.error(request, 'Timeout enviando email. El servidor SMTP no responde a tiempo.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('tickets:admin_email_test')
