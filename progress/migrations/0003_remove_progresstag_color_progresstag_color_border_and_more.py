# Generated by Django 5.0.1 on 2024-12-09 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('progress', '0002_alter_progresstagcustomer_tag_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='progresstag',
            name='color',
        ),
        migrations.AddField(
            model_name='progresstag',
            name='color_border',
            field=models.CharField(default='ffffff', max_length=255),
        ),
        migrations.AddField(
            model_name='progresstag',
            name='color_fill',
            field=models.CharField(default='ffffff', max_length=255),
        ),
        migrations.AddField(
            model_name='progresstag',
            name='color_text',
            field=models.CharField(default='ffffff', max_length=255),
        ),
    ]
