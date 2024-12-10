# Generated by Django 5.0.1 on 2024-12-10 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zns', '0003_alter_znsfieldvoucher_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='zns',
            name='note',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='zns',
            name='status',
            field=models.CharField(choices=[('DRAFT', 'Nháp'), ('PENDING_REVIEW', 'Đang duyệt'), ('APPROVED', 'Đã duyệt'), ('REJECTED', 'Đã từ chối'), ('LOCKED', 'Bị khóa')], default='DRAFT', max_length=20),
        ),
    ]