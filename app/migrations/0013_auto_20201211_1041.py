# Generated by Django 2.0.13 on 2020-12-11 01:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20201209_1648'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingdata',
            name='place',
            field=models.ForeignKey(default='0001', on_delete=django.db.models.deletion.CASCADE, to='app.Place'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='billingdata',
            name='agent',
        ),
        migrations.AddField(
            model_name='billingdata',
            name='agent',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Agent'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='billingdata',
            name='product',
        ),
        migrations.AddField(
            model_name='billingdata',
            name='product',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Product'),
            preserve_default=False,
        ),
    ]
