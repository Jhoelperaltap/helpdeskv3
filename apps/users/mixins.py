from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(UserPassesTestMixin):
    """Base mixin for role-based access control"""
    required_roles = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.role in self.required_roles
    
    def handle_no_permission(self):
        raise PermissionDenied("No tienes permisos para acceder a esta página.")

class SuperAdminRequiredMixin(RoleRequiredMixin):
    required_roles = ['SUPERADMIN']

class TechnicianRequiredMixin(RoleRequiredMixin):
    required_roles = ['TECHNICIAN', 'SUPERADMIN']

class CompanyAdminRequiredMixin(RoleRequiredMixin):
    required_roles = ['COMPANY_ADMIN', 'SUPERADMIN']

class EmployeeOrAboveMixin(RoleRequiredMixin):
    required_roles = ['EMPLOYEE', 'COMPANY_ADMIN', 'TECHNICIAN', 'SUPERADMIN']
