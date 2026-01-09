# core/views.py
from django.views.generic import ListView, CreateView, TemplateView, FormView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone

import csv
import io
import decimal

from .models import Invoice, Client, Project, Category
from .forms import InvoiceForm, CSVUploadForm
from .utils.forecast import forecast_monthly
from .utils.importer import import_invoices_from_file  # сервис (ниже)
from plotly.offline import plot
import plotly.graph_objs as go


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'core/invoice_list.html'
    paginate_by = 20

    def get_queryset(self):
        return Invoice.objects.filter(owner=self.request.user).select_related('project', 'category')


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'core/invoice_form.html'
    success_url = reverse_lazy('core:invoice_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(owner=request.user)
        data = forecast_monthly(invoices, months_ahead=6)
        historic = data['historic']
        forecast = data['forecast']
        fig = go.Figure()
        if not historic.empty:
            fig.add_trace(go.Scatter(x=historic['month'], y=historic['value'], mode='lines+markers', name='Historic'))
        if not forecast.empty:
            fig.add_trace(go.Scatter(x=forecast['month'], y=forecast['value'], mode='lines+markers', name='Forecast'))
        plot_div = plot(fig, output_type='div', include_plotlyjs=False)
        return render(request, self.template_name, {'plot_div': plot_div})


class CSVUploadView(LoginRequiredMixin, FormView):
    template_name = 'core/upload.html'
    form_class = CSVUploadForm
    success_url = reverse_lazy('core:invoice_upload')

    def form_valid(self, form):
        uploaded_file = form.cleaned_data['file']
        result = import_invoices_from_file(uploaded_file, owner=self.request.user)
        self.request.session['import_result'] = result
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        result = self.request.session.pop('import_result', None)
        ctx['import_result'] = result
        return ctx


class ExportInvoicesCSVView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(owner=request.user).select_related('project', 'category')
        response = HttpResponse(content_type='text/csv')
        fname = f"invoices_{request.user.username}_{timezone.now().date()}.csv"
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        writer = csv.writer(response)
        writer.writerow(['date', 'amount', 'client', 'project', 'category', 'paid', 'external_id', 'description'])
        for inv in invoices:
            writer.writerow([
                inv.date.isoformat(),
                f"{inv.amount}",
                inv.project.client.name if inv.project and inv.project.client else '',
                inv.project.title if inv.project else '',
                inv.category.name if inv.category else '',
                'True' if inv.paid else 'False',
                inv.external_id,
                inv.description or '',
            ])
        return response


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
