# Generated by Django 4.0.5 on 2022-07-01 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactdata',
            name='company_email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]