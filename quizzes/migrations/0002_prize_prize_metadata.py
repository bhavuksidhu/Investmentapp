# Generated by Django 4.1.3 on 2022-11-25 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="prize",
            name="prize_metadata",
            field=models.JSONField(blank=True, null=True),
        ),
    ]