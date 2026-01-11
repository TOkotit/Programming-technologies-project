from django.test import TestCase
from django.contrib.auth import get_user_model
from core.utils.importer import import_invoices_from_file
from io import BytesIO

User = get_user_model()

class ImporterTest(TestCase):
    def setUp(self):
        self.u = User.objects.create_user('t','t@t.com','pass')

    def test_import_valid(self):
        csv_content = b"date,amount,client,project,category,paid,external_id,description\n2025-01-01,100,Client A,Proj,Cat,True,ID1,Desc\n"
        f = BytesIO(csv_content)
        res = import_invoices_from_file(f, owner=self.u)
        self.assertEqual(res['created'], 1)
        self.assertEqual(res['skipped'], 0)
