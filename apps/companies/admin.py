from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'email', 'phone_number', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'email']
