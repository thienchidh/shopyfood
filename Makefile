# The name of the Docker Compose service
SERVICE_NAME = bot

# Run the Docker Compose service
run:
	docker-compose up -d $(SERVICE_NAME)

# Stop the Docker Compose service
stop:
	docker-compose down

# View the logs of the Docker Compose service
logs:
	docker-compose logs $(SERVICE_NAME)

# Build the Docker Compose service
build:
	docker-compose build $(SERVICE_NAME)
