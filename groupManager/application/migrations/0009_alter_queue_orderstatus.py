# Generated by Django 5.1.1 on 2024-11-16 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0008_rename_write_mode_queuelist_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queue',
            name='orderStatus',
            field=models.IntegerField(),
        ),
    ]