# Generated by Django 5.1.1 on 2024-11-16 15:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0007_queuelist_title_alter_user_group'),
    ]

    operations = [
        migrations.RenameField(
            model_name='queuelist',
            old_name='write_mode',
            new_name='type',
        ),
    ]
