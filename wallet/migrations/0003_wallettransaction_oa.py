# Generated by Django 5.0.1 on 2024-11-18 09:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0002_alter_wallettransaction_used_at'),
        ('zalo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallettransaction',
            name='oa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='zalo.zalooa'),
        ),
    ]
