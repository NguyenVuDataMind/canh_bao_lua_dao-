.PHONY: help build build-clean up down restart logs clean clean-docker

help:
	@echo "Available commands:"
	@echo "  make build            - Build Docker images"
	@echo "  make build-clean      - Clean old images then build (recommended)"
	@echo "  make up               - Start services"
	@echo "  make down             - Stop services"
	@echo "  make restart          - Restart services"
	@echo "  make logs             - View logs"
	@echo "  make clean            - Remove all containers and volumes"
	@echo "  make clean-docker     - Deep clean Docker (images, cache, volumes)"

build:
	DOCKER_BUILDKIT=1 docker-compose build

build-clean:
	@echo "🧹 Cleaning old Docker images and cache..."
	@docker image prune -f || true
	@docker builder prune -f || true
	@echo "🔨 Building Docker images with BuildKit..."
	@DOCKER_BUILDKIT=1 docker-compose build
	@echo "✓ Build completed! Old images cleaned."

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

clean-docker:
	@echo "🧹 Deep cleaning Docker..."
	@echo "Stopping containers..."
	@docker-compose down -v || true
	@echo "Removing unused images..."
	@docker image prune -a -f || true
	@echo "Removing build cache..."
	@docker builder prune -a -f || true
	@echo "Removing unused volumes..."
	@docker volume prune -f || true
	@echo "Removing unused networks..."
	@docker network prune -f || true
	@echo "System prune..."
	@docker system prune -a -f --volumes || true
	@echo "✓ Deep clean completed!"
