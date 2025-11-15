.PHONY: help build up down restart logs clean train-model verify-model build-with-model

help:
	@echo "Available commands:"
	@echo "  make train-model      - Train PhoBERT model (run before build)"
	@echo "  make verify-model     - Verify trained model exists and is valid"
	@echo "  make build            - Build Docker images"
	@echo "  make build-with-model - Train model then build Docker images"
	@echo "  make up               - Start services"
	@echo "  make down             - Stop services"
	@echo "  make restart          - Restart services"
	@echo "  make logs             - View logs"
	@echo "  make clean            - Remove all containers and volumes"

train-model:
	@echo "Training PhoBERT model..."
	@python scripts/finetune_phobert.py
	@echo "✓ Model training completed!"

verify-model:
	@echo "Verifying model..."
	@python scripts/verify_model.py

build:
	docker-compose build

build-with-model: train-model verify-model build
	@echo "✓ Model trained and Docker image built successfully!"

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
