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
        
        smtp_connection_status = self.test_smtp_connection()
        
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
    
    def test_smtp_connection(self):
        """
        Prueba la conexión SMTP real usando la configuración del .env
        """
        from django.core.mail import get_connection
        import os
        
        try:
            # Crear conexión SMTP directa usando variables de entorno
            smtp_connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=os.environ.get('EMAIL_HOST', ''),
                port=int(os.environ.get('EMAIL_PORT', 587)),
                username=os.environ.get('EMAIL_HOST_USER', ''),
                password=os.environ.get('EMAIL_HOST_PASSWORD', ''),
                use_tls=os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true',
            )
            
            # Verificar que tenemos configuración
            if not smtp_connection.username or not smtp_connection.password:
                return {
                    'success': False,
                    'error': 'Configuración SMTP incompleta. Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en .env',
                    'details': {
                        'host': smtp_connection.host,
                        'port': smtp_connection.port,
                        'username': smtp_connection.username,
                        'has_password': bool(smtp_connection.password),
                        'use_tls': smtp_connection.use_tls,
                    }
                }
            
            # Probar conexión real
            smtp_connection.open()
            smtp_connection.close()
            
            return {
                'success': True,
                'message': f'Conexión SMTP exitosa a {smtp_connection.host}:{smtp_connection.port}',
                'details': {
                    'host': smtp_connection.host,
                    'port': smtp_connection.port,
                    'username': smtp_connection.username,
                    'has_password': bool(smtp_connection.password),
                    'use_tls': smtp_connection.use_tls,
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            suggestions = []
            
            if 'authentication failed' in error_msg.lower():
                suggestions.append('Verifica que EMAIL_HOST_PASSWORD sea una App Password válida de Gmail')
            elif 'connection refused' in error_msg.lower():
                suggestions.append('Verifica la configuración del host SMTP y puerto')
            elif 'tls' in error_msg.lower():
                suggestions.append('Verifica la configuración TLS')
            elif 'timeout' in error_msg.lower():
                suggestions.append('Verifica la conexión a internet y firewall')
            
            return {
                'success': False,
                'error': error_msg,
                'suggestions': suggestions,
                'details': {
                    'host': os.environ.get('EMAIL_HOST', ''),
                    'port': os.environ.get('EMAIL_PORT', '587'),
                    'username': os.environ.get('EMAIL_HOST_USER', ''),
                    'has_password': bool(os.environ.get('EMAIL_HOST_PASSWORD', '')),
                }
            }

    def post(self, request, *args, **kwargs):
        """Manejar envío de emails de prueba con configuración SMTP forzada"""
        from django.core.mail import send_mail, EmailMessage, get_connection
        from django.conf import settings
        import os
        
        test_type = request.POST.get('test_type')
        recipient_email = request.POST.get('recipient_email', 'test@example.com')
        
        # Crear conexión SMTP directa usando variables de entorno
        smtp_connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=os.environ.get('EMAIL_HOST', settings.EMAIL_HOST),
            port=int(os.environ.get('EMAIL_PORT', settings.EMAIL_PORT)),
            username=os.environ.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
            password=os.environ.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD),
            use_tls=os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true',
        )
        
        # Verificar que tenemos configuración SMTP
        if not smtp_connection.username or not smtp_connection.password:
            messages.error(request, '❌ Configuración SMTP incompleta. Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en tu archivo .env')
            return redirect('tickets:admin_email_test')
        
        # Mostrar información sobre la configuración que se usará
        messages.info(request, f'🔧 Usando configuración SMTP: {smtp_connection.host}:{smtp_connection.port} con usuario {smtp_connection.username}')
        
        try:
            # Probar conexión primero
            smtp_connection.open()
            messages.success(request, '✅ Conexión SMTP establecida correctamente')
            smtp_connection.close()
            
            if test_type == 'connection':
                messages.success(request, f'✅ Prueba de conexión SMTP exitosa a {smtp_connection.host}:{smtp_connection.port}')
                messages.info(request, f'🔧 Usuario: {smtp_connection.username} | TLS: {"Habilitado" if smtp_connection.use_tls else "Deshabilitado"}')
                return redirect('tickets:admin_email_test')
            
            if test_type == 'basic':
                message_body = f"""
¡Hola!

Este es un email de prueba básico del sistema de helpdesk.

Configuración SMTP utilizada:
- Host: {smtp_connection.host}:{smtp_connection.port}
- Usuario: {smtp_connection.username}
- TLS: {'Habilitado' if smtp_connection.use_tls else 'Deshabilitado'}
- Enviado desde: {os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)}

✅ Si recibes este mensaje, la configuración SMTP está funcionando correctamente.

¡Saludos!
Sistema Helpdesk
                """
                
                send_mail(
                    subject='[Helpdesk] ✅ Prueba Básica SMTP - Configuración Exitosa',
                    message=message_body,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    recipient_list=[recipient_email],
                    connection=smtp_connection,
                    fail_silently=False,
                )
                messages.success(request, f'✅ Email básico enviado exitosamente a {recipient_email}')
                
            elif test_type == 'html':
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>✅ Prueba SMTP Exitosa - Helpdesk</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 28px; }}
                        .content {{ padding: 30px; }}
                        .success-badge {{ background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin: 10px 0; font-weight: bold; }}
                        .config-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                        .config-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
                        .config-item:last-child {{ border-bottom: none; }}
                        .check-list {{ list-style: none; padding: 0; }}
                        .check-list li {{ padding: 8px 0; }}
                        .check-list li:before {{ content: "✅"; margin-right: 10px; }}
                        .footer {{ background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; }}
                        .footer strong {{ color: white; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎉 Configuración SMTP Exitosa</h1>
                            <p>Sistema de Helpdesk - Prueba de Email HTML</p>
                        </div>
                        <div class="content">
                            <div class="success-badge">✅ SMTP Funcionando Correctamente</div>
                            
                            <p>¡Excelente! Si estás viendo este email con formato HTML, significa que:</p>
                            
                            <ul class="check-list">
                                <li>La configuración SMTP está funcionando perfectamente</li>
                                <li>Gmail está permitiendo el envío de emails</li>
                                <li>Las credenciales son correctas y válidas</li>
                                <li>El sistema puede enviar emails HTML con estilos</li>
                                <li>La conexión TLS está funcionando</li>
                            </ul>
                            
                            <div class="config-box">
                                <h3 style="margin-top: 0; color: #374151;">📋 Configuración SMTP Utilizada:</h3>
                                <div class="config-item">
                                    <span><strong>Host SMTP:</strong></span>
                                    <span>{smtp_connection.host}:{smtp_connection.port}</span>
                                </div>
                                <div class="config-item">
                                    <span><strong>Usuario:</strong></span>
                                    <span>{smtp_connection.username}</span>
                                </div>
                                <div class="config-item">
                                    <span><strong>TLS:</strong></span>
                                    <span>{'✅ Habilitado' if smtp_connection.use_tls else '❌ Deshabilitado'}</span>
                                </div>
                                <div class="config-item">
                                    <span><strong>From Email:</strong></span>
                                    <span>{os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)}</span>
                                </div>
                            </div>
                            
                            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 15px; margin: 20px 0;">
                                <p style="margin: 0; color: #065f46; font-weight: bold;">🚀 ¡Todo está listo para producción!</p>
                                <p style="margin: 5px 0 0 0; color: #047857;">Tu sistema de helpdesk puede enviar notificaciones reales por email.</p>
                            </div>
                        </div>
                        <div class="footer">
                            <p><strong>Sistema Helpdesk</strong> - Prueba de Configuración SMTP</p>
                            <p style="font-size: 12px;">Enviado automáticamente desde el panel de administración</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                email = EmailMessage(
                    subject='[Helpdesk] 🎉 Prueba HTML SMTP - ¡Configuración Exitosa!',
                    body=html_content,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    to=[recipient_email],
                    connection=smtp_connection,
                )
                email.content_subtype = 'html'
                email.send()
                
                messages.success(request, f'✅ Email HTML enviado exitosamente a {recipient_email}')
                
            elif test_type == 'notification':
                # Simular notificación de ticket
                ticket = Ticket.objects.first()
                if ticket:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>🎫 Notificación de Ticket</title>
                        <style>
                            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                            .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                            .header {{ background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 30px 20px; text-align: center; }}
                            .content {{ padding: 30px; }}
                            .ticket-box {{ background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #dc2626; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                            .priority-high {{ color: #dc2626; font-weight: bold; }}
                            .priority-medium {{ color: #d97706; font-weight: bold; }}
                            .priority-low {{ color: #059669; font-weight: bold; }}
                            .footer {{ background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>🎫 Notificación de Ticket</h1>
                                <p>Sistema de Helpdesk</p>
                            </div>
                            <div class="content">
                                <p>Hola <strong>{request.user.get_full_name() or request.user.username}</strong>,</p>
                                <p>El ticket <strong>#{ticket.id}</strong> ha sido actualizado:</p>
                                
                                <div class="ticket-box">
                                    <h3 style="margin-top: 0; color: #374151;">{ticket.title}</h3>
                                    <p><strong>Estado:</strong> <span style="background: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{ticket.get_status_display()}</span></p>
                                    <p><strong>Prioridad:</strong> <span class="priority-{ticket.priority.lower()}">{ticket.get_priority_display()}</span></p>
                                    <p><strong>Empresa:</strong> {ticket.company.name}</p>
                                    <p><strong>Asignado a:</strong> {ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Sin asignar'}</p>
                                    <p><strong>Creado:</strong> {ticket.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                                    
                                    <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
                                        <p style="margin: 0;"><strong>Descripción:</strong></p>
                                        <p style="margin: 5px 0 0 0; color: #6b7280;">{ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}</p>
                                    </div>
                                </div>
                                
                                <p>Puedes ver más detalles del ticket accediendo al sistema de helpdesk.</p>
                                
                                <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                                    <p style="margin: 0; color: #1e40af; font-weight: bold;">💡 Esta es una prueba de notificación</p>
                                    <p style="margin: 5px 0 0 0; color: #1d4ed8;">El sistema SMTP está funcionando correctamente para enviar notificaciones reales.</p>
                                </div>
                            </div>
                            <div class="footer">
                                <p><strong>Sistema Helpdesk</strong></p>
                                <p style="font-size: 12px;">Este es un email automático, no responder.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    email = EmailMessage(
                        subject=f'[Helpdesk] 🎫 Ticket #{ticket.id} - {ticket.title}',
                        body=html_content,
                        from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                        to=[recipient_email],
                        connection=smtp_connection,
                    )
                    email.content_subtype = 'html'
                    email.send()
                    
                    messages.success(request, f'✅ Notificación de ticket enviada exitosamente a {recipient_email}')
                else:
                    messages.error(request, '❌ No hay tickets disponibles para la prueba')
                    
            elif test_type == 'bulk':
                users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')[:3]  # Limitar a 3 para pruebas
                sent_count = 0
                failed_count = 0
                
                for user in users:
                    try:
                        send_mail(
                            subject='[Helpdesk] 📧 Prueba Masiva - Sistema de Notificaciones',
                            message=f"""
Hola {user.get_full_name() or user.username},

Este es un email de prueba masiva del sistema de helpdesk.

Tu información:
- Usuario: {user.username}
- Email: {user.email}
- Rol: {user.get_role_display()}
- Empresa: {user.company.name if user.company else 'Sin empresa'}

✅ Esta prueba verifica que el sistema puede enviar notificaciones masivas correctamente usando SMTP real.

Configuración SMTP utilizada:
- Host: {smtp_connection.host}:{smtp_connection.port}
- Usuario: {smtp_connection.username}

¡El sistema está listo para enviar notificaciones reales!

Saludos,
Sistema Helpdesk
                            """,
                            from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                            recipient_list=[user.email],
                            connection=smtp_connection,
                            fail_silently=False,
                        )
                        sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        print(f"Error enviando email a {user.email}: {str(e)}")
                
                if sent_count > 0:
                    messages.success(request, f'✅ Emails masivos enviados exitosamente a {sent_count} usuarios')
                if failed_count > 0:
                    messages.warning(request, f'⚠️ {failed_count} emails fallaron en el envío')
                    
            else:
                messages.error(request, '❌ Tipo de prueba no válido')
                
        except Exception as e:
            messages.error(request, f'❌ Error enviando email: {str(e)}')
            print(f"Error detallado: {str(e)}")
            
            # Sugerencias específicas para errores comunes
            error_str = str(e).lower()
            if 'authentication failed' in error_str:
                messages.error(request, '💡 Verifica que EMAIL_HOST_PASSWORD sea una App Password válida de Gmail')
            elif 'connection refused' in error_str:
                messages.error(request, '💡 Verifica la configuración del host SMTP y puerto')
            elif 'tls' in error_str:
                messages.error(request, '💡 Verifica la configuración TLS')
        
        return redirect('tickets:admin_email_test')
