# Generated by Django 4.0.5 on 2022-09-14 11:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0010_tip_active'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tip',
            old_name='active',
            new_name='is_active',
        ),
    ]
