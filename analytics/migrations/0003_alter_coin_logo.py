# Generated by Django 4.2.6 on 2025-02-23 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_remove_coin_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coin',
            name='logo',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
