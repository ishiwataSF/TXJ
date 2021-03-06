# Generated by Django 2.0.13 on 2020-12-07 10:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20201207_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingdata',
            name='amount',
            field=models.FloatField(default=111),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billingdata',
            name='billing_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billingdata',
            name='total',
            field=models.IntegerField(default=1111),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billingdata',
            name='unit_place',
            field=models.FloatField(default=1111),
            preserve_default=False,
        ),
    ]
