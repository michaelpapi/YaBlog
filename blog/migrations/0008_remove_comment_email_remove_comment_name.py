# Generated by Django 5.1.1 on 2024-10-10 17:42

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0007_comment_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="comment",
            name="email",
        ),
        migrations.RemoveField(
            model_name="comment",
            name="name",
        ),
    ]
