# Generated by Django 5.0.1 on 2024-11-20 09:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0011_alter_reward_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 19, 9, 13, 3, 140659, tzinfo=datetime.timezone.utc)),
        ),
    ]