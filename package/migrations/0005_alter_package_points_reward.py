# Generated by Django 5.0.1 on 2024-11-29 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0004_alter_price_type_alter_price_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='points_reward',
            field=models.BigIntegerField(default=0),
        ),
    ]
