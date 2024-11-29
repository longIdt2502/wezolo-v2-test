# Generated by Django 5.0.1 on 2024-11-29 06:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0037_alter_sessions_created_at_alter_sessions_login_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessions',
            name='created_at',
            field=models.DateTimeField(verbose_name=datetime.datetime(2024, 11, 29, 6, 27, 10, 56375, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='login_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 29, 6, 27, 10, 56341, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='verify',
            name='expired_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 29, 6, 28, 40, 56180, tzinfo=datetime.timezone.utc)),
        ),
    ]
