# Generated by Django 4.0.5 on 2022-07-27 02:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_remove_transaction_zerodha_transaction_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='order_type',
            field=models.TextField(default='MARKET'),
        ),
    ]