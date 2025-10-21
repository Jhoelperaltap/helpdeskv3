from django.urls import path
from .views import (
    HomeRedirectView, UserLoginView, UserLogoutView, 
    AdminUserCreateView, AdminUserListView, AdminUserEditView, AdminPasswordChangeView,
    UserProfileView, UserPasswordChangeView  # Importando nuevas vistas
)

app_name = 'users'

urlpatterns = [
    path('', HomeRedirectView.as_view(), name='home'),
    path('home/', HomeRedirectView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin_create_user'),
    path('admin/users/<int:pk>/edit/', AdminUserEditView.as_view(), name='admin_edit_user'),
    path('admin/users/<int:pk>/change-password/', AdminPasswordChangeView.as_view(), name='admin_change_password'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/change-password/', UserPasswordChangeView.as_view(), name='user_change_password'),
]
