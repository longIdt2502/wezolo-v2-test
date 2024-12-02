# Generated by Django 5.0.1 on 2024-11-29 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points_earned', models.IntegerField(default=0)),
                ('expiration_date', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'Reward',
                'db_table': 'reward',
            },
        ),
        migrations.CreateModel(
            name='RewardBenefit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benefit_name', models.TextField()),
                ('benefit_description', models.TextField(blank=True, null=True)),
                ('type', models.CharField(blank=True, choices=[('ZNS', 'Đơn giá gửi ZNS'), ('CREATE_OA', 'Tạo zalo OA'), ('CONNECT_OA', 'Kết nối zalo OA'), ('CREATE_WS', 'Tạo wordspace'), ('OA_PREMIUM', 'Nâng cấp OA Premium'), ('MESS', 'Tin nhắn vượt khung'), ('START', 'Phí khởi tạo')], max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'RewardBenefit',
                'db_table': 'reward_benefit',
            },
        ),
        migrations.CreateModel(
            name='RewardTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, choices=[('BRONZE', 'Đồng'), ('SILVER', 'Bạc'), ('GOLD', 'Vàng'), ('PLATINUM', 'Bạch kim')], max_length=255, null=True)),
                ('code', models.CharField(blank=True, max_length=255, null=True)),
                ('min_points', models.BigIntegerField(default=0)),
                ('benefit_description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'RewardTier',
                'db_table': 'reward_tier',
            },
        ),
    ]
