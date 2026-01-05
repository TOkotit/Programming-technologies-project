from django.urls import path
from .views import InvoiceListView, InvoiceCreateView, DashboardView, SignUpView


app_name = 'core'


urlpatterns = [
    path('', DashboardView.as_view(), name='home'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/new/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('signup/', SignUpView.as_view(), name='signup'),
]