# Generated by Django 4.0.5 on 2022-07-27 01:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0005_rename_uuid_passwordreset_uid'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adminnotification',
            options={'ordering': ['-created_at']},
        ),
    ]