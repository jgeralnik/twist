#!/bin/bash

# If -v is passed to the script, docker volumes will be erased
if [ "$1" == "-v" ]; then
    docker compose -f docker-compose.dev.yml down -v
else
    docker compose -f docker-compose.dev.yml down
fi

docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
docker exec -it twist-django-1 bash -c "./manage.py runserver 0.0.0.0:8000"
