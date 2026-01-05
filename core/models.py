from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()




class Client(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True)


    def __str__(self):
        return self.name


class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return self.title




class Category(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)


    def __str__(self):
        return self.name




class Invoice(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='invoices')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='invoices')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    external_id = models.CharField(max_length=200, blank=True, help_text="id из CSV/платформы")


    class Meta:
        ordering = ['-date']


    def __str__(self):
        return f"{self.date} — {self.amount}"