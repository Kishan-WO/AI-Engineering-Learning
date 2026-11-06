# Docker Basics

Docker packages an application and its dependencies into an image that runs the same way on any machine.

A `Dockerfile` describes how to build the image. A container is a running instance of an image. Docker Compose starts several containers together, such as an API, a PostgreSQL database and a Redis cache, from one `docker-compose.yml` file.

Keep images small by using slim base images and multi-stage builds.
