# Generated by Django 5.1.1 on 2024-11-09 21:03

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0003_alter_authorize_session_token_alter_queue_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorize',
            name='session_token',
            field=models.TextField(default=uuid.uuid4, editable=False),
        ),
    ]
