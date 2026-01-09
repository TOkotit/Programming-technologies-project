# core/management/commands/import_invoices.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os

from core.utils.importer import import_invoices_from_file

User = get_user_model()

class Command(BaseCommand):
    help = "Import invoices from CSV. Usage: python manage.py import_invoices path/to/file.csv --username USERNAME"

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to CSV file')
        parser.add_argument('--username', type=str, help='Owner username for created objects (optional)')

    def handle(self, *args, **options):
        csvfile = options['csvfile']
        username = options.get('username')

        if not os.path.exists(csvfile):
            raise CommandError(f"File not found: {csvfile}")

        owner = None
        if username:
            try:
                owner = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User not found: {username}")
        else:
            owner = User.objects.filter(is_superuser=True).first()

        if owner is None:
            raise CommandError("Owner not specified and no superuser found. Use --username.")

        with open(csvfile, 'rb') as f:
            result = import_invoices_from_file(f, owner=owner)

        self.stdout.write(self.style.SUCCESS(f"Created: {result['created']}, Skipped: {result['skipped']}"))
        if result['errors']:
            for e in result['errors']:
                self.stdout.write(self.style.ERROR(e))
