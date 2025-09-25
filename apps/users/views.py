from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import RegisterForm, AdminUserCreateForm
from .models import User
from apps.companies.models import Company
from apps.notifications.utils import notify_user_created
import secrets
import string

class SuperAdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires user to be superadmin"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superadmin():
            raise PermissionDenied("Solo los super administradores pueden acceder a esta página.")
        return super().dispatch(request, *args, **kwargs)

class HomeRedirectView(LoginRequiredMixin, TemplateView):
    template_name = 'users/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superadmin():
                return redirect('dashboard:dashboard')
            elif request.user.is_technician():
                return redirect('tickets:ticket_list')
            elif request.user.is_company_admin():
                return redirect('dashboard:dashboard')
            else:  # EMPLOYEE
                return redirect('tickets:ticket_list')
        return super().dispatch(request, *args, **kwargs)

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    
    def form_invalid(self, form):
        form.data = form.data.copy()
        form.data['password'] = ''  # Clear password field
        messages.error(self.request, 'Credenciales incorrectas. Por favor, verifica tu usuario y contraseña.')
        return super().form_invalid(form)
    
    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            form.data = form.data.copy()
            form.data['password'] = ''
            messages.error(self.request, 'Tu cuenta está desactivada. Contacta al administrador.')
            return self.form_invalid(form)
        
        messages.success(self.request, f'¡Bienvenido, {user.first_name or user.username}!')
        return super().form_valid(form)
    
    def get_success_url(self):
        user = self.request.user
        if user.is_superadmin():
            return reverse_lazy('dashboard:dashboard')
        elif user.is_technician():
            return reverse_lazy('tickets:ticket_list')
        elif user.is_company_admin():
            return reverse_lazy('dashboard:dashboard')
        else:  # EMPLOYEE
            return reverse_lazy('tickets:ticket_list')

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('landing:home')
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle both GET and POST requests properly"""
        if request.method == 'GET':
            # For GET requests, perform logout immediately
            messages.info(request, 'Has cerrado sesión exitosamente.')
            return super().dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for logout"""
        return self.post(request, *args, **kwargs)

def generate_temporary_password(length=12):
    """Generate a secure temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

class AdminUserCreateView(SuperAdminRequiredMixin, CreateView):
    """Admin-only view to create new users"""
    template_name = 'users/admin_create_user.html'
    form_class = AdminUserCreateForm
    success_url = reverse_lazy('users:admin_user_list')
    model = User
    
    def form_valid(self, form):
        temp_password = generate_temporary_password()
        user = form.save(commit=False)
        user.set_password(temp_password)
        user.save()
        
        # Send welcome email with temporary password
        notify_user_created(user, temp_password, self.request.user)
        
        messages.success(
            self.request, 
            f'Usuario {user.username} creado exitosamente. Se ha enviado un email con las credenciales de acceso.'
        )
        return redirect(self.success_url)

class AdminUserListView(SuperAdminRequiredMixin, ListView):
    """Admin-only view to list all users"""
    model = User
    template_name = 'users/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.select_related('company').order_by('-date_joined')
