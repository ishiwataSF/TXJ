from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
import os


class Staff(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.author)


class Customer(models.Model):
    customer_name = models.CharField(max_length=200)

    def __str__(self):
        return self.customer_name


class GeneratedData(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    author = models.ForeignKey(Staff, on_delete=models.CASCADE)
    UPLOAD_NOT_COMPLETED = 0
    CSV_OUTPUT_COMPLETED = 1
    VISUALLY_CONFIRMED = 2
    IMPORT_DATA_OUTPUT_COMPLETED = 3
    STATUS = (
        (UPLOAD_NOT_COMPLETED, 'upload not completed'),
        (CSV_OUTPUT_COMPLETED, 'csv output completed'),
        (VISUALLY_CONFIRMED, 'visually confirmed'),
        (IMPORT_DATA_OUTPUT_COMPLETED, 'import_data output completed'),
    )
    status = models.IntegerField(choices=STATUS)


class MatchedData(models.Model):
    generated = models.OneToOneField(GeneratedData, on_delete=models.CASCADE)
    author = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    brycen_file = models.FileField(upload_to='brycen_file/%Y/%m%d/', validators=[FileExtensionValidator(['xlsx', ])]) # ブライセンの契約データExcelを保存したい
    billing_file = models.FileField(upload_to='billing_file/%Y/%m%d/', validators=[FileExtensionValidator(['csv', ])]) # 電子データCSVを保存したい
    matched_data_file = models.FileField(upload_to='matched_data_file/%Y/%m%d/',
                                         validators=[FileExtensionValidator(['csv', ])], null=True,blank=True) # 突合済CSVを保存したい

    @property
    def billing_filename(self):
        return os.path.basename(self.billing_file.name)

    @property
    def matched_data_filename(self):
        return os.path.basename(self.matched_data_file.name)


class VisuallyMatchedData(models.Model):
    matched = models.OneToOneField(MatchedData, on_delete=models.CASCADE)
    author = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)


class ImportData(models.Model):
    visually_matched = models.OneToOneField(VisuallyMatchedData, on_delete=models.CASCADE)
    author = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    visually_matched_file = models.FileField(upload_to='visually_matched_file/%Y/%m%d/',
                                             validators=[FileExtensionValidator(['csv', ])], null=True,blank=True) # 突合済CSV修正ありなら、修正版CSVを保存したい。無い場合もあり。
    import_data_file = models.FileField(upload_to='import_data_file/%Y/%m%d/', validators=[FileExtensionValidator(['xlsx', ])],
                                        null=True,blank=True) # インポートデータExcelを保存したい