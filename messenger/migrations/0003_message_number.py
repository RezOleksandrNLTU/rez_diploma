# Generated by Django 4.0.6 on 2022-07-09 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0002_chat_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='number',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
