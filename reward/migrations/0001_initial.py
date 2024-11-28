# Generated by Django 5.0.1 on 2024-11-15 09:39

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wallet', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RewardTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, choices=[('SILVER', 'Bạc'), ('GOLD', 'Vàng'), ('PLATINUM', 'Bạch kim')], max_length=255, null=True)),
                ('min_points', models.IntegerField(default=0)),
                ('benefit_description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'RewardTier',
                'db_table': 'reward_tier',
            },
        ),
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points_earned', models.IntegerField(default=0)),
                ('expiration_date', models.DateTimeField(default=datetime.datetime(2025, 5, 14, 9, 39, 31, 781663, tzinfo=datetime.timezone.utc))),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField()),
                ('customer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wallet.wallettransaction')),
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
                ('type', models.CharField(blank=True, choices=[('ZNS', 'Đơn giá gửi ZNS'), ('CREATE_OA', 'Tạo zalo OA'), ('CONNECT_OA', 'Kết nối zalo OA'), ('CREATE_WS', 'Tạo wordspace'), ('OA_PREMIUM', 'Nâng cấp OA Premium')], max_length=255, null=True)),
                ('value', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField()),
                ('tier_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reward.rewardtier')),
            ],
            options={
                'verbose_name': 'RewardBenefit',
                'db_table': 'reward_benefit',
            },
        ),
    ]