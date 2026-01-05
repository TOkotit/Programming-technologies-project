from django import forms
from .models import Invoice




class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['project', 'category', 'date', 'amount', 'paid', 'description', 'external_id']


    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Amount must be a positive number')
        return amount