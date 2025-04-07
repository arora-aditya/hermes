
backend: backend/*
	fastapi dev backend/main.py

frontend:
	cd frontend && npm run dev

