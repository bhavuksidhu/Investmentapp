# Generated by Django 4.0.5 on 2022-07-22 05:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_stocks_index_listing_alter_stocks_series'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Stocks',
            new_name='Stock',
        ),
    ]