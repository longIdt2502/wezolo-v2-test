# Generated by Django 5.0.1 on 2024-11-18 06:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reward', '0005_alter_reward_expiration_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reward',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 17, 6, 27, 30, 580615, tzinfo=datetime.timezone.utc)),
        ),
    ]