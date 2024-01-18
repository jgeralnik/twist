#!/usr/bin/env python
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twist.settings")
django.setup()

from django.contrib.auth import get_user_model
from flags.state import enable_flag

from song_signup.views import name_to_username
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command


ALON_USER = ('Alon', 'Aviv', '76697421')
SHANI_USER = ('Shani', 'Wahrman', '76697421')


def create_superuser(first_name, last_name, password):
    User = get_user_model()
    username = name_to_username(first_name, last_name)
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email='',
            password=password,
            first_name=first_name,
            last_name=last_name
        )


if __name__ == '__main__':
    if os.getenv('INIT', 'true'):
        call_command('migrate')

    create_superuser(*ALON_USER)
    create_superuser(*SHANI_USER)

    singers_group, _ = Group.objects.get_or_create(name='singers')
    singers_group.permissions.add(Permission.objects.get(codename='view_songrequest'))
    enable_flag('CAN_SIGNUP')