#!/bin/bash


# Build the Docker images without using cache
docker-compose --env-file .env.development build --no-cache

# Then start the services
docker-compose --env-file .env.development up