# Generated by Django 3.1.2 on 2022-07-04 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0011_auto_20220703_2039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='songrequest',
            name='cycle',
            field=models.FloatField(blank=True, null=True),
        ),
    ]