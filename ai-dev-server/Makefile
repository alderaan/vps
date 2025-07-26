.PHONY: help dev dev-bg stop test health docs docker-build docker-deploy docker-local

help:
	@echo "Available commands:"
	@echo "  dev         - Start development server"
	@echo "  dev-bg      - Start development server in background"
	@echo "  stop        - Stop background server"
	@echo "  test        - Test server endpoints"
	@echo "  health      - Check server health"
	@echo "  docs        - Open API documentation"
	@echo "  docker-build - Build and push Docker image"
	@echo "  docker-deploy - Deploy with docker-compose"
	@echo "  docker-local - Run locally with Docker"

dev:
	uv run server.py

dev-bg:
	nohup uv run server.py > server.log 2>&1 & echo $$!

stop:
	pkill -f server.py

test:
	curl -s http://127.0.0.1:8080/health
	curl -s http://127.0.0.1:8080/docs

health:
	curl -s http://127.0.0.1:8080/health

docs:
	open http://127.0.0.1:8080/docs

docker-deploy:
	docker buildx build --platform linux/amd64 -t registry.correlion.ai/ai-dev-server:latest --push .

docker-local:
	docker build -t ai-dev-server .
	docker run -p 8080:8080 ai-dev-server