# Docker 
dev:
	docker compose up --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f api

dev-reset:
	docker compose down -v
	docker compose up --build