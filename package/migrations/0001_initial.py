# Generated by Django 5.0.1 on 2024-11-15 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.IntegerField(default=0)),
                ('validity', models.DateTimeField()),
                ('points_reward', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Package',
                'db_table': 'package',
            },
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('ZNS', 'Đơn giá gửi ZNS'), ('CREATE_OA', 'Tạo zalo OA'), ('CONNECT_OA', 'Kết nối zalo OA'), ('CREATE_WS', 'Tạo wordspace'), ('OA_PREMIUM', 'Nâng cấp OA Premium')], default='ZNS', max_length=255)),
                ('value', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'Price',
                'db_table': 'price',
            },
        ),
    ]