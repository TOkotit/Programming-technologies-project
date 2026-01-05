from django.views.generic import ListView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from .models import Invoice
from .forms import InvoiceForm
from .utils.forecast import forecast_monthly
from django.shortcuts import render
from plotly.offline import plot
import plotly.graph_objs as go




class InvoiceListView(ListView):
    model = Invoice
    template_name = 'core/invoice_list.html'
    paginate_by = 20


    def get_queryset(self):
        return Invoice.objects.all().select_related('project', 'category')



class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'core/invoice_form.html'
    success_url = reverse_lazy('core:invoice_list')


    def form_valid(self, form):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        form.instance.owner = User.objects.first()
        return super().form_valid(form)




class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'


    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.all()
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

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'