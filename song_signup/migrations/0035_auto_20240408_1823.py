# Generated by Django 3.1.2 on 2024-04-08 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0034_auto_20240408_1812'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupsongrequest',
            name='default_lyrics',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupsongrequest',
            name='found_music',
            field=models.BooleanField(default=False),
        ),
    ]
