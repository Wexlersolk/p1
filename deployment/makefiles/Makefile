BACKEND_IMAGE=p1-backend:latest
FRONTEND_IMAGE=p1-frontend:latest

BACKEND_DOCKERFILE=deployment/docker/backend/Dockerfile
FRONTEND_DOCKERFILE=deployment/docker/frontend/Dockerfile

BACKEND_CONTAINER=p1-backend
FRONTEND_CONTAINER=p1-frontend

BACKEND_PORT=8000
FRONTEND_PORT=80

CONTEXT=../..

.PHONY: help build run start stop clean

help:
	@echo "Targets:"
	@echo "  make build           - Build all images"
	@echo "  make build-backend   - Build backend image"
	@echo "  make build-frontend  - Build frontend image"
	@echo "  make run             - Run all containers"
	@echo "  make start           - Start stopped containers"
	@echo "  make stop            - Stop containers"
	@echo "  make clean           - Remove containers and images"

build-%:
	cd $(CONTEXT) && docker build -t p1-$*:latest -f deployment/docker/$*/Dockerfile .

build: build-backend build-frontend

run-%:
	docker run -d -p $($*_PORT):$($*_PORT) --name p1-$* p1-$*:latest

run: run-backend run-frontend

start-%:
	docker start p1-$*

stop-%:
	docker stop p1-$*

start: start-backend start-frontend
stop: stop-backend stop-frontend

clean:
	docker rm -f $(BACKEND_CONTAINER) $(FRONTEND_CONTAINER) || true
	docker rmi $(BACKEND_IMAGE) $(FRONTEND_IMAGE) || true
