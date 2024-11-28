# Generated by Django 5.0.1 on 2024-11-16 08:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_alter_sessions_created_at_alter_sessions_login_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessions',
            name='created_at',
            field=models.DateTimeField(verbose_name=datetime.datetime(2024, 11, 16, 8, 17, 43, 899303, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='login_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 16, 8, 17, 43, 899272, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='verify',
            name='expired_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 16, 8, 19, 13, 897859, tzinfo=datetime.timezone.utc)),
        ),
    ]