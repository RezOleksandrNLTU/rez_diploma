# Generated by Django 4.0.6 on 2022-07-12 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0004_profile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, upload_to='static/messenger/profile_images'),
        ),
    ]
