# Generated by Django 4.0.5 on 2022-07-05 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_user_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zerodhadata',
            name='access_token',
            field=models.TextField(default='', null=True),
        ),
        migrations.AlterField(
            model_name='zerodhadata',
            name='enctoken',
            field=models.TextField(default='', null=True),
        ),
        migrations.AlterField(
            model_name='zerodhadata',
            name='public_token',
            field=models.TextField(default='', null=True),
        ),
        migrations.AlterField(
            model_name='zerodhadata',
            name='refresh_token',
            field=models.TextField(default='', null=True),
        ),
    ]