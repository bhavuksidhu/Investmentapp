# Generated by Django 4.0.5 on 2022-07-21 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_marketquote_name_alter_zerodhadata_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stocks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.TextField()),
                ('symbol', models.TextField()),
                ('series', models.TextField()),
                ('index_listing', models.TextField()),
            ],
        ),
    ]