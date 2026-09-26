.PHONY: install test dev-api dev-web

VENV=.venv

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	cd backend && ../$(VENV)/bin/pytest

dev-api:
	cd backend && ../$(VENV)/bin/uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev
