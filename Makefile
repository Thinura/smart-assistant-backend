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