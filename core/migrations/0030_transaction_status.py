# Generated by Django 4.0.5 on 2022-07-29 00:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_zerodhadata_funds'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='status',
            field=models.TextField(default='Pending'),
        ),
    ]