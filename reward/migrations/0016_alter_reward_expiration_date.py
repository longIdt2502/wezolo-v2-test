# Generated by Django 5.0.1 on 2024-11-26 09:15

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0015_alter_reward_expiration_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 25, 9, 15, 5, 874091, tzinfo=datetime.timezone.utc)),
        ),
    ]
