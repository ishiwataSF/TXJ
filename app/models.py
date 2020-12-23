from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
import os


class Staff(models.Model):
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.staff}'


class Customer(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.name}'


class Place(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.code} {self.name}'


class Agent(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.code} {self.name}'


class Product(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.code} {self.name}'


class GeneratedData(models.Model):
    update_date = models.DateTimeField(default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
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
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    brycen_file = models.FileField(upload_to='brycen_file/%Y/%m%d/', validators=[FileExtensionValidator(['xlsx', ])]) # ブライセンの契約データExcelを保存したい
    billing_file = models.FileField(upload_to='billing_file/%Y/%m%d/', validators=[FileExtensionValidator(['csv', ])], null=True, blank=True) # 電子データCSVを保存したい
    matched_data_file = models.FileField(upload_to='matched_data_file/%Y/%m%d/',
                                         validators=[FileExtensionValidator(['csv', ])], null=True,blank=True) # 突合済CSVを保存したい
    @property
    def brycen_filename(self):
        return os.path.basename(self.brycen_file.name)

    @property
    def billing_filename(self):
        return os.path.basename(self.billing_file.name)

    @property
    def matched_data_filename(self):
        return os.path.basename(self.matched_data_file.name)


class BillingData(models.Model):
    created_date = models.DateTimeField(default=timezone.now)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    matched = models.ForeignKey(MatchedData, on_delete=models.CASCADE)
    billing_date = models.DateField()
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.FloatField()
    unit_price = models.FloatField()
    total = models.IntegerField()

    WOOD_PALLET_ITEM_NUM = 0
    CONTAINER_REPLACEMENT_ITEM_NUM = 1
    CONTAINER_RENTAL_ITEM_NUM = 2
    STRETCH_FILM_ITEM_NUM = 3
    SLUDGES_ITEM_NUM = 4
    SCRAP_ITEM_NUM = 7
    GENERAL_WASTE_ITEM_NUM = 9
    INDUSTRIAL_WASTE_ITEM_NUM = 10
    MANIFEST_ITEM_NUM = 11
    WASTE_ELEMENT_ITEM_NUM = 12
    WASTE_TIRE_ITEM_NUM = 13
    BASE_TIRE_ITEM_NUM = 14
    WASTE_COOLANT_ITEM_NUM = 15
    WASTE_OIL_ITEM_NUM = 16
    INDUSTRIAL_WASTE_TAX_ITEM_NUM = 17
    WASTE_BATTERY_ITEM_NUM = 18

    ITEM = (
        (WOOD_PALLET_ITEM_NUM, '木パレット'),
        (CONTAINER_REPLACEMENT_ITEM_NUM, 'コンテナ交換'),
        (CONTAINER_RENTAL_ITEM_NUM, 'コンテナレンタル代'),
        (STRETCH_FILM_ITEM_NUM, 'ストレッチフィルム'),
        (SLUDGES_ITEM_NUM, '汚泥'),
        (SCRAP_ITEM_NUM, 'スクラップ類'),
        (GENERAL_WASTE_ITEM_NUM, '一般廃棄物'),
        (INDUSTRIAL_WASTE_ITEM_NUM, '産業廃棄物'),
        (MANIFEST_ITEM_NUM, 'マニフェスト'),
        (WASTE_ELEMENT_ITEM_NUM, '廃エレメント'),
        (WASTE_TIRE_ITEM_NUM, '廃タイヤ'),
        (BASE_TIRE_ITEM_NUM, '台タイヤ'),
        (WASTE_COOLANT_ITEM_NUM, '廃クーラント'),
        (WASTE_OIL_ITEM_NUM, '廃油'),
        (INDUSTRIAL_WASTE_TAX_ITEM_NUM, '産廃税'),
        (WASTE_BATTERY_ITEM_NUM, '廃バッテリー'),
    )

    item = models.IntegerField(choices=ITEM)

    KG_UNIT_NUM = 0
    CAR_UNIT_NUM = 1
    ONESET_UNIT_NUM = 2
    MONTHLY_UNIT_NUM = 3
    CUBIC_METER_UNIT_NUM = 4
    TIMES_UNIT_NUM = 5
    CASE_UNIT_NUM = 6
    PEDESTAL_UNIT_NUM = 7
    TIRE_UNIT_NUM = 8
    LITER_UNIT_NUM = 9
    SHEET_UNIT_NUM = 10
    METER_UNIT_NUM = 12
    QUANTITY_UNIT_NUM = 13

    UNIT = (
        (KG_UNIT_NUM, 'kg'),
        (CAR_UNIT_NUM, '車'),
        (ONESET_UNIT_NUM, '式'),
        (MONTHLY_UNIT_NUM, '月額'),
        (CUBIC_METER_UNIT_NUM, '立米'),
        (TIMES_UNIT_NUM, '回'),
        (CASE_UNIT_NUM, 'ケース'),
        (PEDESTAL_UNIT_NUM, '台'),
        (TIRE_UNIT_NUM, '本'),
        (LITER_UNIT_NUM, 'リットル'),
        (SHEET_UNIT_NUM, '枚'),
        (METER_UNIT_NUM, 'メートル'),
        (QUANTITY_UNIT_NUM, '個'),
    )

    unit = models.IntegerField(choices=UNIT)


class VisuallyMatchedData(models.Model):
    matched = models.OneToOneField(MatchedData, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)


class ImportData(models.Model):
    visually_matched = models.OneToOneField(VisuallyMatchedData, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    visually_matched_file = models.FileField(upload_to='visually_matched_file/%Y/%m%d/',
                                             validators=[FileExtensionValidator(['csv', ])], null=True,blank=True) # 突合済CSV修正ありなら、修正版CSVを保存したい。無い場合もあり。
    import_data_file = models.FileField(upload_to='import_data_file/%Y/%m%d/', validators=[FileExtensionValidator(['xlsx', ])],
                                        null=True,blank=True) # インポートデータExcelを保存したい

    @property
    def visually_matched_filename(self):
        return os.path.basename(self.visually_matched_file.name)

    @property
    def import_data_filename(self):
        return os.path.basename(self.import_data_file.name)