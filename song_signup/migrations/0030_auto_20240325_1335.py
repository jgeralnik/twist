# Generated by Django 3.1.2 on 2024-03-25 13:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0029_songrequest_skipped'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ticketorder',
            old_name='is_freebee',
            new_name='is_freebie',
        ),
    ]