# Generated by Django 4.2.1 on 2023-06-16 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0021_alter_group_information'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='information',
            field=models.TextField(blank=True, help_text='Заповнювати у форматі:\nПосилання: https://www.google.com.ua/', verbose_name='Посилання'),
        ),
    ]
