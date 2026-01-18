# core/utils/importer.py
import csv
from django.utils.dateparse import parse_date
from django.db import transaction
from decimal import Decimal, InvalidOperation

from core.models import Client, Project, Category, Invoice

REQUIRED_COLUMNS = {'date', 'amount', 'client', 'project', 'category', 'paid', 'external_id'}


def import_invoices_from_file(fileobj, owner):
    result = {'created': 0, 'skipped': 0, 'errors': []}
    decoded = (line.decode('utf-8') if isinstance(line, (bytes, bytearray)) else line for line in fileobj)
    reader = csv.DictReader(decoded)
    headers = set(reader.fieldnames or [])
    if not REQUIRED_COLUMNS.issubset(headers):
        result['errors'].append(f"CSV must contain columns: {', '.join(sorted(REQUIRED_COLUMNS))}")
        return result

    with transaction.atomic():
        for i, row in enumerate(reader, start=1):
            try:
                date = parse_date(row.get('date', '').strip())
                if date is None:
                    raise ValueError("Invalid date (use YYYY-MM-DD)")
                try:
                    amount = Decimal(row.get('amount', '').strip())
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                except (InvalidOperation, ValueError) as e:
                    raise ValueError("Invalid amount: " + str(e))

                paid = str(row.get('paid', '')).strip().lower() in ('1', 'true', 'yes', 'y')
                client_name = row.get('client', '').strip() or 'Unknown'
                project_title = row.get('project', '').strip() or 'Default project'
                category_name = row.get('category', '').strip() or 'Uncategorized'
                external_id = row.get('external_id', '').strip()
                description = row.get('description', '').strip()

                client_obj, _ = Client.objects.get_or_create(owner=owner, name=client_name)
                project_obj, _ = Project.objects.get_or_create(owner=owner, client=client_obj, title=project_title)
                category_obj, _ = Category.objects.get_or_create(owner=owner, name=category_name)

                if external_id:
                    exists = Invoice.objects.filter(owner=owner, external_id=external_id).exists()
                    if exists:
                        result['skipped'] += 1
                        continue

                Invoice.objects.create(
                    owner=owner,
                    project=project_obj,
                    category=category_obj,
                    date=date,
                    amount=amount,
                    paid=paid,
                    description=description,
                    external_id=external_id,
                )
                result['created'] += 1
            except Exception as e:
                result['errors'].append(f"Line {i}: {e}")
    return result
