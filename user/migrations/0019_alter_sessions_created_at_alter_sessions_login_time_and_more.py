# Generated by Django 5.0.1 on 2024-11-26 09:15

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_alter_sessions_created_at_alter_sessions_login_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessions',
            name='created_at',
            field=models.DateTimeField(verbose_name=datetime.datetime(2024, 11, 26, 9, 15, 5, 864635, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='login_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 26, 9, 15, 5, 864603, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='verify',
            name='expired_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 26, 9, 16, 35, 864450, tzinfo=datetime.timezone.utc)),
        ),
    ]
