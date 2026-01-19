from django.test import TestCase
from django.contrib.auth import get_user_model
from core.utils.forecast import forecast_monthly
from core.models import Invoice
from datetime import date

User = get_user_model()

class ForecastTest(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username='testuser', password='pass')
        Invoice.objects.create(owner=self.u, date=date(2024,1,1), amount=100)
        Invoice.objects.create(owner=self.u, date=date(2024,2,1), amount=200)
        Invoice.objects.create(owner=self.u, date=date(2024,3,1), amount=300)
        Invoice.objects.create(owner=self.u, date=date(2024,4,1), amount=400)
        Invoice.objects.create(owner=self.u, date=date(2024,5,1), amount=500)
        Invoice.objects.create(owner=self.u, date=date(2024,6,1), amount=600)

    def test_forecast_outputs(self):
        qs = Invoice.objects.filter(owner=self.u)
        res = forecast_monthly(qs, months_ahead=3)
        self.assertIn('historic', res)
        self.assertIn('forecast', res)
        historic = res['historic']
        forecast = res['forecast']
        self.assertFalse(historic.empty)
        self.assertEqual(len(forecast), 3)
