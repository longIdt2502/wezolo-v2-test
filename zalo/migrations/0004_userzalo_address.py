# Generated by Django 5.0.1 on 2024-12-05 02:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_wezoloappconfig'),
        ('zalo', '0003_rename_oa_id_zalooa_uid_zalo_oa'),
    ]

    operations = [
        migrations.AddField(
            model_name='userzalo',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user.address'),
        ),
    ]
