TEST_DATABASE_URL=postgresql+psycopg://smart_user:smart_password@localhost:5432/smart_assistant_test

docker-compose-up:
	docker-compose up -d

migrate:
	poetry run alembic upgrade head

migrate-test:
	ALEMBIC_DATABASE_URL=$(TEST_DATABASE_URL) poetry run alembic upgrade head

migrate-all:
	poetry run alembic upgrade head
	ALEMBIC_DATABASE_URL=$(TEST_DATABASE_URL) poetry run alembic upgrade head

test:
	poetry run pytest

lint:
	poetry run ruff check .

fix:
	poetry run ruff check . --fix

format:
	poetry run ruff format .

run:
	poetry run uvicorn app.main:app --reload

reset-test-db:
	docker exec -it smart-assistant-postgres psql -U smart_user -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'smart_assistant_test';"
	docker exec -it smart-assistant-postgres psql -U smart_user -d postgres -c "DROP DATABASE IF EXISTS smart_assistant_test;"
	docker exec -it smart-assistant-postgres psql -U smart_user -d postgres -c "CREATE DATABASE smart_assistant_test OWNER smart_user;"

reset-test-db-migrate: reset-test-db
	$(MAKE) migrate-test

send-outbox:
	curl -X POST http://localhost:8000/api/v1/outbox/send-pending \
		-H "Content-Type: application/json" \
		-d '{"limit": 50, "include_failed": true}'
		