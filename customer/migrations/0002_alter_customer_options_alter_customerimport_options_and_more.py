# Generated by Django 5.0.1 on 2024-12-03 10:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
        ('zalo', '0003_rename_oa_id_zalooa_uid_zalo_oa'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customer',
            options={'verbose_name': 'Customer'},
        ),
        migrations.AlterModelOptions(
            name='customerimport',
            options={'verbose_name': 'CustomerImport'},
        ),
        migrations.RemoveField(
            model_name='customer',
            name='code',
        ),
        migrations.AlterModelTable(
            name='customer',
            table='customer',
        ),
        migrations.AlterModelTable(
            name='customerimport',
            table='customer_import',
        ),
        migrations.CreateModel(
            name='CustomerUserZalo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='customer.customer')),
                ('oa', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zalo.zalooa')),
                ('user_zalo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zalo.userzalo')),
            ],
            options={
                'verbose_name': 'CustomerUserZalo',
                'db_table': 'customer_user_zalo',
            },
        ),
    ]
