.PHONY: help install dev build test clean docker-up docker-down

help:
	@echo "Clinical Trial Intelligence Platform - Make Commands"
	@echo ""
	@echo "  install          Install all dependencies"
	@echo "  dev              Start development servers"
	@echo "  build            Build production artifacts"
	@echo "  test             Run all tests"
	@echo "  clean            Clean build artifacts"
	@echo "  docker-up        Start all services with Docker Compose"
	@echo "  docker-down      Stop all Docker services"
	@echo "  docker-logs      View Docker logs"
	@echo ""

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing infrastructure dependencies..."
	cd infrastructure && pip install -r requirements.txt

dev:
	@echo "Starting development servers..."
	docker-compose up postgres redis weaviate -d
	@echo "Waiting for services to be ready..."
	sleep 5
	@echo "Starting backend on http://localhost:8000"
	@echo "Starting frontend on http://localhost:3000"
	@echo "Run 'cd backend && uvicorn app.main:app --reload' in one terminal"
	@echo "Run 'cd frontend && npm run dev' in another terminal"

build:
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Build complete!"

test:
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm run lint

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

docker-up:
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d
	@echo "Services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

docker-down:
	@echo "Stopping all Docker services..."
	docker-compose down

docker-logs:
	docker-compose logs -f
