# Generated by Django 5.1.1 on 2024-11-09 21:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0002_alter_authorize_session_token_alter_user_group_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorize',
            name='session_token',
            field=models.TextField(default='<function uuid4 at 0x000001AE91F8D940>', editable=False),
        ),
        migrations.AlterField(
            model_name='queue',
            name='user',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='application.user'),
        ),
        migrations.AlterField(
            model_name='user',
            name='group',
            field=models.ForeignKey(default=None, null=True, on_delete=models.SET(0), to='application.group'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='application.userrole'),
        ),
    ]
