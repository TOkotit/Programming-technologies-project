from django.contrib import admin
from .models import Client, Project, Category, Invoice


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'email')
    search_fields = ('name', 'email')




@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'owner', 'hourly_rate')
    search_fields = ('title', 'client__name')




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ('name',)




@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('date', 'owner', 'project', 'amount', 'paid', 'external_id')
    search_fields = ('project__title', 'owner__username', 'external_id')
    list_filter = ('paid', 'date', 'category')