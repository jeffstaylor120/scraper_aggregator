# Makefile — all targets use Docker. Dev = hot reload via docker-compose.dev.yml.
# Run from repo root. Set .env for OPENAI_API_KEY etc.

.PHONY: dev prod down frontend build-frontend

# Full stack in dev: api + frontend with hot reload (code mounted).
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Full stack in prod mode (no hot reload).
prod:
	docker compose up --build

# Stop and remove containers.
down:
	docker compose down

# Rebuild frontend image and recreate container (e.g. after adding npm deps like react-markdown).
# Stop/rm frontend so its node_modules volume is recreated from the new image; then up.
build-frontend:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml build frontend --no-cache
	docker compose -f docker-compose.yml -f docker-compose.dev.yml stop frontend
	docker compose -f docker-compose.yml -f docker-compose.dev.yml rm -f frontend
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run Vite frontend locally (optional). With make dev, frontend runs in Docker at :5173 with hot reload.
frontend:
	cd frontend && npm run dev
