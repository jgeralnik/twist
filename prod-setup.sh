#!/bin/bash
python manage.py migrate
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
