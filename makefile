.PHONY: help build up down logs shell mongo-shell clean dev prod

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the application
	docker-compose build

up: ## Start the application in production mode
	docker-compose up -d

down: ## Stop the application
	docker-compose down

logs: ## View application logs
	docker-compose logs -f

shell: ## Open shell in the application container
	docker-compose exec app bash

mongo-shell: ## Open MongoDB shell
	docker-compose exec mongo mongosh -u admin -p password123

clean: ## Clean up containers and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d

dev-logs: ## View development logs
	docker-compose -f docker-compose.dev.yml logs -f

dev-down: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

prod: ## Start production environment
	docker-compose -f docker-compose.yml up -d

restart: ## Restart the application
	docker-compose restart app

status: ## Show container status
	docker-compose ps

backup: ## Backup MongoDB data
	docker-compose exec mongo mongodump --username admin --password password123 --authenticationDatabase admin --out /tmp/backup
	docker cp $$(docker-compose ps -q mongo):/tmp/backup ./backup

restore: ## Restore MongoDB data from backup
	docker cp ./backup $$(docker-compose ps -q mongo):/tmp/
	docker-compose exec mongo mongorestore --username admin --password password123 --authenticationDatabase admin /tmp/backup