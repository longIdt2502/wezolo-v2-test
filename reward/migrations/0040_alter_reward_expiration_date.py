# Generated by Django 5.0.1 on 2024-11-29 06:56

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0039_alter_reward_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 28, 6, 56, 41, 732496, tzinfo=datetime.timezone.utc)),
        ),
    ]
