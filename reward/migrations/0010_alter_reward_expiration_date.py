# Generated by Django 5.0.1 on 2024-11-19 08:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0009_alter_reward_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 18, 8, 40, 6, 781918, tzinfo=datetime.timezone.utc)),
        ),
    ]
