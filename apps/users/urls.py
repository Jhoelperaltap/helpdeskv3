from django.urls import path
from .views import (
    HomeRedirectView, UserLoginView, UserLogoutView, 
    AdminUserCreateView, AdminUserListView
)

app_name = 'users'

urlpatterns = [
    path('', HomeRedirectView.as_view(), name='home'),
    path('home/', HomeRedirectView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin_create_user'),
]
