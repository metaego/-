# Generated by Django 3.2.25 on 2024-04-26 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_last_login'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_password',
            field=models.TextField(),
        ),
    ]
