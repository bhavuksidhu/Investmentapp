# Generated by Django 4.0.5 on 2022-07-27 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_transaction_order_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='executed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='transaction',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]