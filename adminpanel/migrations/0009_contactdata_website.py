# Generated by Django 4.0.5 on 2022-09-14 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0008_tip'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactdata',
            name='website',
            field=models.TextField(default=''),
        ),
    ]
