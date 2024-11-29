# Generated by Django 5.0.1 on 2024-11-29 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ACTIVE', 'Đang hoạt động'), ('INACTIVE', 'Tạm nghỉ'), ('TERMINATED', 'Nghỉ việc')], default='ACTIVE', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeOa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'EmployeeOa',
                'db_table': 'employee_oa',
            },
        ),
        migrations.CreateModel(
            name='EmployeeUserZalo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'EmployeeUserZalo',
                'db_table': 'employee_userzalo',
            },
        ),
    ]
