# Generated by Django 4.0.5 on 2022-07-26 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_remove_marketquote_data_from_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketquote',
            name='company_name',
            field=models.TextField(default='', null=True),
        ),
    ]