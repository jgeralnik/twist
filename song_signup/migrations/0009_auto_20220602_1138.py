# Generated by Django 3.2.13 on 2022-06-02 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0008_songrequest_is_bonus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='songrequest',
            name='is_bonus',
        ),
        migrations.AlterField(
            model_name='songrequest',
            name='cycle',
            field=models.FloatField(blank=True, null=True),
        ),
    ]