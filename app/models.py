from django.conf import settings
from django.db import models
from django.utils import timezone


class Staff(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Customer(models.Model):
    customer_name = models.CharField(max_length=200)

    def __str__(self):
        return self.customer_name

class GenerateData(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    STATUS = (
        (0,'upload not completed'),
        (1, 'csv output completed'),
        (2, 'visually confirmed'),
        (3, 'import_data output completed'),
    )
    status = models.IntegerField(choices=STATUS)

    def __int__(self):
        return self.status

class MatchedData(models.Model):
    generated = models.OneToOneField(GenerateData, on_delete=models.CASCADE)
    author = models.OneToOneField(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    brycen_file = models.FileField() # ブライセンの契約データExcelを保存したい
    billing_file = models.FileField() # 電子データCSVを保存したい
    created_file = models.FileField() # 突合済CSVを保存したい

class VisuallyMachedData(models.Model):
    matched = models.OneToOneField(MatchedData, on_delete=models.CASCADE)
    author = models.OneToOneField(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)

class ImportData(models.Model):
    visually_matched = models.OneToOneField(VisuallyMachedData, on_delete=models.CASCADE)
    author = models.OneToOneField(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    upload_file = models.FileField(null=True, blank=True)  # 突合済CSV修正ありなら、修正版CSVを保存したい。無い場合もあり。
    created_file = models.FileField() # インポートデータExcelを保存したい


