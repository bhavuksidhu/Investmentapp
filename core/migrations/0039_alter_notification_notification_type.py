# Generated by Django 4.0.5 on 2022-08-18 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_usersetting_show_after_trade_modal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('News', 'News'), ('Stock-Listing', 'Stock-Listing'), ('Purchase', 'Purchase'), ('Sale', 'Sale'), ('Subscription', 'Subscription'), ('Others', 'Others')], default='', max_length=20),
        ),
    ]
