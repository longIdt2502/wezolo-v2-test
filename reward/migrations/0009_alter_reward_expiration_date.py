# Generated by Django 5.0.1 on 2024-11-18 09:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0008_alter_reward_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 17, 9, 6, 40, 361662, tzinfo=datetime.timezone.utc)),
        ),
    ]