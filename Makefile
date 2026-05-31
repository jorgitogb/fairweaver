SHELL := /bin/bash

BACKEND_PORT := 8000
FRONTEND_PORT := 5173

.PHONY: dev kill install lint test docker docker-kill clean

dev:
	@trap 'kill 0' SIGINT SIGTERM EXIT; \
		echo "→ Starting backend (port $(BACKEND_PORT))..."; \
		cd backend && uv run uvicorn main:app --reload & \
		echo "→ Starting frontend (port $(FRONTEND_PORT))..."; \
		cd frontend && npm run dev & \
		wait

kill:
	@for port in $(BACKEND_PORT) $(FRONTEND_PORT); do \
		pid=$$(lsof -ti :$$port 2>/dev/null); \
		if [ -n "$$pid" ]; then \
			kill -9 $$pid 2>/dev/null && echo "✓ Port $$port freed" || true; \
		fi; \
	done

install:
	@echo "→ Installing backend deps..."; \
	(cd backend && uv sync); \
	echo "→ Installing frontend deps..."; \
	(cd frontend && npm install); \
	echo "✓ Install complete"

lint:
	@echo "→ Linting backend..."; \
	(cd backend && uv run ruff check .); \
	echo "→ Typechecking frontend..."; \
	(cd frontend && npm run typecheck); \
	echo "✓ Lint complete"

test:
	@echo "→ Running backend tests..."; \
	(cd backend && uv run pytest -v); \
	echo "→ Running frontend tests..."; \
	(cd frontend && npm test); \
	echo "→ Running frontend typecheck..."; \
	(cd frontend && npm run typecheck); \
	echo "✓ Tests complete"

docker:
	docker compose up

docker-kill:
	docker compose down
