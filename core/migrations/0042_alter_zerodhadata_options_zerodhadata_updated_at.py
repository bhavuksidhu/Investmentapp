# Generated by Django 4.0.5 on 2022-09-12 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_alter_zerodhadata_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='zerodhadata',
            options={'ordering': ['-updated_at']},
        ),
        migrations.AddField(
            model_name='zerodhadata',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
