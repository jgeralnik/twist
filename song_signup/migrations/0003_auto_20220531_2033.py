# Generated by Django 3.2.13 on 2022-05-31 20:33

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import song_signup.managers


class Migration(migrations.Migration):

    dependencies = [
        ('song_signup', '0002_auto_20220531_1820'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='singer',
            managers=[
                ('cycles', song_signup.managers.ThreeCycleOrdering()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RenameField(
            model_name='singer',
            old_name='cycle1_position',
            new_name='cy1_position',
        ),
        migrations.RenameField(
            model_name='singer',
            old_name='cycle2_position',
            new_name='cy2_position',
        ),
        migrations.RenameField(
            model_name='singer',
            old_name='cycle3_position',
            new_name='cy3_position',
        ),
        migrations.AlterField(
            model_name='songrequest',
            name='additional_singers',
            field=models.ManyToManyField(blank=True, related_name='songs_as_additional', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='songrequest',
            name='singer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='songs', to=settings.AUTH_USER_MODEL),
        ),
    ]
