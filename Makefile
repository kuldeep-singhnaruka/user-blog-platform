.PHONY: install test dev-api dev-web

install:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	cd backend && ../.venv/bin/pytest

dev-api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev
