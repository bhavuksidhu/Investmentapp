# Generated by Django 4.0.5 on 2022-08-02 01:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_transaction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='zerodha_postback',
            field=models.JSONField(null=True),
        ),
    ]