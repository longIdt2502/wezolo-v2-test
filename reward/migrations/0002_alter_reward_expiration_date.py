# Generated by Django 5.0.1 on 2024-11-16 06:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 15, 6, 40, 55, 800470, tzinfo=datetime.timezone.utc)),
        ),
    ]