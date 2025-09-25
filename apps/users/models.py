from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.companies.models import Company

class User(AbstractUser):
    ROLES = [
        ('EMPLOYEE', 'Empleado'),
        ('COMPANY_ADMIN', 'Admin Empresa'),
        ('TECHNICIAN', 'Técnico'),
        ('SUPERADMIN', 'Super Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES, default='EMPLOYEE')
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name='users')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def is_company_admin(self):
        return self.role == 'COMPANY_ADMIN'
    
    def is_technician(self):
        return self.role == 'TECHNICIAN'
    
    def is_superadmin(self):
        return self.role == 'SUPERADMIN'
    
    def is_employee(self):
        return self.role == 'EMPLOYEE'
    
    def can_manage_company(self):
        """Check if user can manage company-level operations"""
        return self.is_company_admin() or self.is_superadmin()
    
    def can_handle_tickets(self):
        """Check if user can handle/resolve tickets"""
        return self.is_technician() or self.is_superadmin()
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
