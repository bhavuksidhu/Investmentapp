# Generated by Django 4.1.3 on 2022-11-22 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0043_rename_exchange_stock_company_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="firebase_token",
            field=models.TextField(blank=True, null=True, unique=True),
        ),
    ]
