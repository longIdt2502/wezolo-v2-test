# Generated by Django 5.0.1 on 2024-11-29 06:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0038_alter_reward_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 28, 6, 43, 30, 334430, tzinfo=datetime.timezone.utc)),
        ),
    ]
