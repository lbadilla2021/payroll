.PHONY: up down logs shell-backend shell-db migrate bootstrap

secret:
	python3 -c "import secrets; print(secrets.token_urlsafe(64))"
	
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f backend

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U saas_user -d saas_db

migrate:
	docker compose exec backend alembic upgrade head

bootstrap:
	docker compose exec backend python -m app.scripts.bootstrap

reset-db:
	@echo "WARNING: This will destroy all data!"
	docker compose down -v
	docker compose up -d

status:
	docker compose ps
