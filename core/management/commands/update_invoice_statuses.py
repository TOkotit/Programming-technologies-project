from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Invoice

class Command(BaseCommand):
    help = 'Mark invoices overdue where date < today and not paid'

    def handle(self, *args, **options):
        today = timezone.localdate()
        qs = Invoice.objects.filter(paid=False, date__lt=today).exclude(status='overdue')
        updated = qs.update(status='overdue')
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} invoices to overdue'))