from django.views.generic import TemplateView, CreateView, ListView, UpdateView, FormView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .forms import RegisterForm, AdminUserCreateForm, AdminUserEditForm, AdminPasswordChangeForm, UserPasswordChangeForm
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
        # El UserCreationForm ya hashea la contraseña correctamente en su método save()
        user = form.save(commit=True)
        
        # Get the password from the form before it's hashed (for the email)
        password = form.cleaned_data.get('password1')
        
        # Send welcome email with the password they set
        notify_user_created(user, password, self.request.user)
        
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
        queryset = User.objects.select_related('company').order_by('-date_joined')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(company__name__icontains=search_query)
            )
        
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        company_filter = self.request.GET.get('company', '')
        if company_filter:
            queryset = queryset.filter(company_id=company_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['company_filter'] = self.request.GET.get('company', '')
        context['roles'] = User.ROLES
        context['companies'] = Company.objects.all()
        return context

class AdminUserEditView(SuperAdminRequiredMixin, UpdateView):
    """Admin-only view to edit existing users"""
    model = User
    form_class = AdminUserEditForm
    template_name = 'users/admin_edit_user.html'
    success_url = reverse_lazy('users:admin_user_list')
    
    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request,
            f'Usuario {user.username} actualizado exitosamente.'
        )
        return redirect(self.success_url)

class AdminPasswordChangeView(SuperAdminRequiredMixin, FormView):
    """Admin-only view to change user passwords"""
    form_class = AdminPasswordChangeForm
    template_name = 'users/admin_change_password.html'
    success_url = reverse_lazy('users:admin_user_list')
    
    def dispatch(self, request, *args, **kwargs):
        self.user_to_change = get_object_or_404(User, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_to_change'] = self.user_to_change
        return context
    
    def form_valid(self, form):
        new_password = form.cleaned_data['new_password1']
        self.user_to_change.set_password(new_password)
        self.user_to_change.save()
        
        messages.success(
            self.request,
            f'Contraseña de {self.user_to_change.username} cambiada exitosamente.'
        )
        return redirect(self.success_url)

class UserProfileView(LoginRequiredMixin, TemplateView):
    """Vista de perfil del usuario autenticado"""
    template_name = 'users/user_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class UserPasswordChangeView(LoginRequiredMixin, FormView):
    """Vista para que los usuarios cambien su propia contraseña"""
    form_class = UserPasswordChangeForm
    template_name = 'users/user_change_password.html'
    success_url = reverse_lazy('users:user_profile')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            'Tu contraseña ha sido cambiada exitosamente. Por favor, inicia sesión nuevamente.'
        )
        # Logout user after password change for security
        from django.contrib.auth import logout
        logout(self.request)
        return redirect('users:login')
