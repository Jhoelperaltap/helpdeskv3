from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from apps.tickets.models import Ticket
from apps.users.models import User
from apps.companies.models import Company
import json
from django.core import serializers
import csv
from django.views import View

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    login_url = '/users/login/'
    redirect_field_name = 'next'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        user = self.request.user
        if user.role == 'COMPANY_ADMIN':
            qs = Ticket.objects.filter(company=user.company)
        elif user.role == 'EMPLOYEE':
            qs = Ticket.objects.filter(Q(company=user.company) | Q(created_by=user))
        elif user.role == 'TECHNICIAN':
            qs = Ticket.objects.filter(Q(assigned_to=user) | Q(company=user.company))
        else:  # SUPERADMIN
            qs = Ticket.objects.all()
        
        # Basic stats
        ctx['total_tickets'] = qs.count()
        ctx['by_status'] = list(qs.values('status').annotate(count=Count('id')))
        ctx['by_priority'] = list(qs.values('priority').annotate(count=Count('id')))
        
        ctx['open_tickets'] = qs.filter(status='OPEN').count()
        ctx['in_progress_tickets'] = qs.filter(status='IN_PROGRESS').count()
        ctx['resolved_tickets'] = qs.filter(status='RESOLVED').count()
        ctx['closed_tickets'] = qs.filter(status='CLOSED').count()
        
        # Performance metrics by technician
        technicians = User.objects.filter(role='TECHNICIAN')
        if user.role != 'SUPERADMIN':
            technicians = technicians.filter(company=user.company)
        
        technician_stats = []
        for tech in technicians:
            tech_tickets = qs.filter(assigned_to=tech)
            resolved_count = tech_tickets.filter(status__in=['RESOLVED', 'CLOSED']).count()
            total_assigned = tech_tickets.count()
            
            technician_stats.append({
                'name': f"{tech.first_name} {tech.last_name}",
                'total_assigned': total_assigned,
                'resolved': resolved_count,
                'resolution_rate': round((resolved_count / total_assigned * 100) if total_assigned > 0 else 0, 1)
            })
        
        ctx['technician_stats'] = technician_stats
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_tickets = qs.filter(created_at__gte=thirty_days_ago).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        ctx['daily_tickets'] = list(daily_tickets)
        
        # Companies list for filter (only for superadmin)
        if user.role == 'SUPERADMIN':
            ctx['companies'] = Company.objects.all()
        
        return ctx

class DashboardDataView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        company_id = request.GET.get('company_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Base queryset with permissions
        if user.role == 'COMPANY_ADMIN':
            qs = Ticket.objects.filter(company=user.company)
        elif user.role == 'EMPLOYEE':
            qs = Ticket.objects.filter(Q(company=user.company) | Q(created_by=user))
        elif user.role == 'TECHNICIAN':
            qs = Ticket.objects.filter(Q(assigned_to=user) | Q(company=user.company))
        else:  # SUPERADMIN
            qs = Ticket.objects.all()
            if company_id:
                qs = qs.filter(company_id=company_id)
        
        # Date filtering
        if date_from:
            qs = qs.filter(created_at__gte=datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            qs = qs.filter(created_at__lte=datetime.strptime(date_to, '%Y-%m-%d'))
        
        data = {
            'total_tickets': qs.count(),
            'by_status': list(qs.values('status').annotate(count=Count('id'))),
            'by_priority': list(qs.values('priority').annotate(count=Count('id'))),
            'open_tickets': qs.filter(status='OPEN').count(),
            'in_progress_tickets': qs.filter(status='IN_PROGRESS').count(),
            'resolved_tickets': qs.filter(status='RESOLVED').count(),
            'closed_tickets': qs.filter(status='CLOSED').count(),
        }
        
        return JsonResponse(data)

class ExportReportView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        export_format = request.GET.get('format', 'csv')
        
        # Get filtered data
        if user.role == 'COMPANY_ADMIN':
            qs = Ticket.objects.filter(company=user.company)
        elif user.role == 'EMPLOYEE':
            qs = Ticket.objects.filter(Q(company=user.company) | Q(created_by=user))
        elif user.role == 'TECHNICIAN':
            qs = Ticket.objects.filter(Q(assigned_to=user) | Q(company=user.company))
        else:  # SUPERADMIN
            qs = Ticket.objects.all()
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="tickets_report.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Título', 'Estado', 'Prioridad', 'Empresa', 'Creado por', 'Asignado a', 'Fecha creación'])
            
            for ticket in qs.select_related('company', 'created_by', 'assigned_to'):
                writer.writerow([
                    ticket.id,
                    ticket.title,
                    ticket.get_status_display(),
                    ticket.get_priority_display(),
                    ticket.company.name if ticket.company else '',
                    f"{ticket.created_by.first_name} {ticket.created_by.last_name}",
                    f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}" if ticket.assigned_to else '',
                    ticket.created_at.strftime('%Y-%m-%d %H:%M')
                ])
            
            return response
        
        return HttpResponse("Formato no soportado", status=400)
