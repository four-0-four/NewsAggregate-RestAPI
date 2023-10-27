#!/bin/bash

# Build the Docker images without using cache for the production setup
docker-compose --env-file .env.production build --no-cache

docker push registry.digitalocean.com/farabix/mainframe:latest
