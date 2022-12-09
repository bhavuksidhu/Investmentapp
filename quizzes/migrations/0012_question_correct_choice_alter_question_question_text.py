# Generated by Django 4.1.3 on 2022-12-02 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0011_questionoption_delete_questionchoice"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="correct_choice",
            field=models.CharField(default="", max_length=250),
        ),
        migrations.AlterField(
            model_name="question",
            name="question_text",
            field=models.CharField(default="", max_length=1000),
        ),
    ]