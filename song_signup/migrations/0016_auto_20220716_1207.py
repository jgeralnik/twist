# Generated by Django 3.1.2 on 2022-07-16 12:07

import django.contrib.auth.models
from django.db import migrations
import song_signup.managers


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0015_singer_placeholder'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='singer',
            managers=[
                ('ordering', song_signup.managers.DisneylandOrdering()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]