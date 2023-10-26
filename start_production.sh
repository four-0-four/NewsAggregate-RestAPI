#!/bin/bash

# Build the Docker images without using cache for the production setup
docker-compose -f docker-compose.production.yml --env-file .env.production build --no-cache

# Then start the services
docker-compose -f docker-compose.production.yml --env-file .env.production up -d