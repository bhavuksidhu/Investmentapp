# Generated by Django 4.0.5 on 2022-08-05 02:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_emailverificationrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='if_not_invest_then_what',
            field=models.TextField(default='', null=True),
        ),
    ]
