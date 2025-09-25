from django.urls import path
from .views import (
    TicketListView, TicketDetailView, TicketCreateView, TicketEditView, 
    ticket_close, ticket_reopen, save_filter, load_filter, delete_filter, clear_filters,
    pause_escalation, resume_escalation_view, escalation_history
)
from .admin_views import (
    EscalationDashboardView, EscalationRuleListView, EscalationRuleCreateView,
    EscalationRuleUpdateView, EscalationRuleDeleteView, EscalationSettingsListView,
    EscalationSettingsCreateView, EscalationSettingsUpdateView, EscalationLogDetailView,
    EscalationReportView, escalation_stats_api, toggle_escalation_rule, bulk_escalation_actions,
    EmailTestView  # Agregando import para vista de pruebas de email
)

app_name = 'tickets'

urlpatterns = [
    path('', TicketListView.as_view(), name='ticket_list'),
    path('create/', TicketCreateView.as_view(), name='ticket_create'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/edit/', TicketEditView.as_view(), name='ticket_edit'),
    path('<int:pk>/close/', ticket_close, name='ticket_close'),
    path('<int:pk>/reopen/', ticket_reopen, name='ticket_reopen'),
    path('filters/save/', save_filter, name='save_filter'),
    path('filters/load/<int:filter_id>/', load_filter, name='load_filter'),
    path('filters/delete/<int:filter_id>/', delete_filter, name='delete_filter'),
    path('filters/clear/', clear_filters, name='clear_filters'),
    path('<int:pk>/escalation/pause/', pause_escalation, name='pause_escalation'),
    path('<int:pk>/escalation/resume/', resume_escalation_view, name='resume_escalation'),
    path('<int:pk>/escalation/history/', escalation_history, name='escalation_history'),
    
    # Admin URLs para escalamiento
    path('admin/escalation/', EscalationDashboardView.as_view(), name='admin_escalation_dashboard'),
    path('admin/escalation/rules/', EscalationRuleListView.as_view(), name='admin_escalation_rules'),
    path('admin/escalation/rules/create/', EscalationRuleCreateView.as_view(), name='admin_escalation_rule_create'),
    path('admin/escalation/rules/<int:pk>/edit/', EscalationRuleUpdateView.as_view(), name='admin_escalation_rule_edit'),
    path('admin/escalation/rules/<int:pk>/delete/', EscalationRuleDeleteView.as_view(), name='admin_escalation_rule_delete'),
    path('admin/escalation/rules/<int:pk>/toggle/', toggle_escalation_rule, name='admin_escalation_rule_toggle'),
    path('admin/escalation/settings/', EscalationSettingsListView.as_view(), name='admin_escalation_settings'),
    path('admin/escalation/settings/create/', EscalationSettingsCreateView.as_view(), name='admin_escalation_settings_create'),
    path('admin/escalation/settings/<int:pk>/edit/', EscalationSettingsUpdateView.as_view(), name='admin_escalation_settings_edit'),
    path('admin/escalation/logs/<int:pk>/', EscalationLogDetailView.as_view(), name='admin_escalation_log_detail'),
    path('admin/escalation/reports/', EscalationReportView.as_view(), name='admin_escalation_reports'),
    path('admin/escalation/stats/', escalation_stats_api, name='admin_escalation_stats'),
    path('admin/escalation/bulk-actions/', bulk_escalation_actions, name='admin_escalation_bulk_actions'),
    path('admin/email-test/', EmailTestView.as_view(), name='admin_email_test'),
]
