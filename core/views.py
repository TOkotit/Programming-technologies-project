from django.views.generic import ListView, CreateView, TemplateView, FormView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import login
import csv
from datetime import date
from django.http import JsonResponse
from django.db.models import Sum, Avg, Count, Q
from .forms import InvoiceForm, CSVUploadForm
from .utils.importer import import_invoices_from_file
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView
from django.shortcuts import render
from django.db.models import Sum, Avg, Count, Q
from django.db.models.functions import TruncMonth
from .models import Invoice
from .utils.forecast import forecast_monthly

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'core/invoice_list.html'
    paginate_by = 20

    def get_queryset(self):
        qs = Invoice.objects.filter(owner=self.request.user).select_related('project', 'category', 'project__client')
        q = self.request.GET

        search = q.get('q')
        if search:
            qs = qs.filter(
                Q(project__title__icontains=search) |
                Q(project__client__name__icontains=search) |
                Q(external_id__icontains=search) |
                Q(description__icontains=search)
            )

        client = q.get('client')
        if client:
            qs = qs.filter(project__client__id=client)

        project = q.get('project')
        if project:
            qs = qs.filter(project__id=project)

        category = q.get('category')
        if category:
            qs = qs.filter(category__id=category)

        paid = q.get('paid')
        if paid in ('1', '0', 'true', 'false', 'True', 'False'):
            if paid.lower() in ('1', 'true'):
                qs = qs.filter(paid=True)
            else:
                qs = qs.filter(paid=False)

        date_from = q.get('date_from')
        date_to = q.get('date_to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        order = q.get('order', '-date')  # default: newest first
        qs = qs.order_by(order)
        return qs


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
        user = request.user
        invoices = Invoice.objects.filter(owner=user)

        agg = invoices.aggregate(
            total=Sum('amount'),
            avg=Avg('amount'),
            count=Count('id'),
            unpaid_count=Count('id', filter=Q(paid=False)),
            unpaid_sum=Sum('amount', filter=Q(paid=False)),
        )

        today = date.today()
        overdue_agg = invoices.filter(paid=False, date__lt=today).aggregate(
            overdue_sum=Sum('amount'),
            overdue_count=Count('id')
        )

        # best month
        best = invoices.annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(total=Sum('amount')) \
            .order_by('-total') \
            .first()
        best_month = best['month'].strftime('%Y-%m') if best and best.get('month') else None

        # Forecast (this function returns lists of dicts already)
        forecast_dict = forecast_monthly(invoices, months_ahead=6)
        historic_data = forecast_dict.get('historic', []) or []
        forecast_data = forecast_dict.get('forecast', []) or []

        # by client for pie
        by_client = invoices.values('project__client__name').annotate(total=Sum('amount')).order_by('-total')
        client_labels = [x['project__client__name'] or 'Unknown' for x in by_client]
        client_values = [float(x['total'] or 0) for x in by_client]

        context = {
            'total_income': float(agg['total'] or 0),
            'avg_amount': float(agg['avg'] or 0),
            'count': int(agg['count'] or 0),
            'unpaid_count': int(agg['unpaid_count'] or 0),
            'unpaid_sum': float(agg['unpaid_sum'] or 0),
            'overdue_sum': float(overdue_agg.get('overdue_sum') or 0),
            'overdue_count': int(overdue_agg.get('overdue_count') or 0),
            'best_month': best_month,
            'historic_data': historic_data,
            'forecast_data': forecast_data,
            'client_labels': client_labels,
            'client_values': client_values,
        }
        return render(request, self.template_name, context)


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

class CSVPreviewView(LoginRequiredMixin, FormView):
    template_name = 'core/upload_preview.html'
    form_class = CSVUploadForm

    def form_valid(self, form):
        f = form.cleaned_data['file']
        decoded = f.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded)
        rows = list(reader)[:50]
        self.request.session['csv_preview'] = f.read().decode('utf-8')  # or better: store bytes
        return render(self.request, 'core/upload_preview.html', {'rows': rows, 'form': form})


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
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('core:dashboard')

    def form_valid(self, form):
        user = form.save()
        self.object = user
        login(self.request, user)
        return redirect(self.get_success_url())


class InvoiceListApiView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        qs = Invoice.objects.filter(owner=request.user).select_related('project', 'category', 'project__client')
        if q:
            qs = qs.filter(
                Q(project__title__icontains=q) |
                Q(project__client__name__icontains=q) |
                Q(external_id__icontains=q) |
                Q(description__icontains=q)
            )
        invoices = qs.order_by('-date')[:200]
        data = []
        for inv in invoices:
            data.append({
                'id': inv.id,
                'date': inv.date.isoformat(),
                'project': inv.project.title if inv.project else '',
                'client': inv.project.client.name if inv.project and inv.project.client else '',
                'category': inv.category.name if inv.category else '',
                'amount': str(inv.amount),
                'paid': bool(inv.paid),
                'external_id': inv.external_id,
                'description': inv.description or '',
            })
        return JsonResponse({'invoices': data})