# Generated by Django 3.2 on 2023-04-15 22:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'ordering': ['-author_id'], 'verbose_name': 'Подписки', 'verbose_name_plural': 'Подписки'},
        ),
    ]
