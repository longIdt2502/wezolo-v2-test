# Generated by Django 5.0.1 on 2024-11-22 03:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0013_alter_reward_expiration_date_alter_reward_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 21, 3, 29, 52, 699917, tzinfo=datetime.timezone.utc)),
        ),
    ]