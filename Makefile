.PHONY: start-mock-services stop-mock-services test-mock-services clean-mock-services


start-mock-services:
	@echo "🚀 Starting mock external services..."
	python -m app.scripts.start_mock
	# python app/scripts/start_mock.py

#(requires separate terminal)
stop-mock-services:
	@echo "🛑 Stopping mock services..."
	pkill -f "mock_services"


test-mock-services:
	@echo "🧪 Testing mock services..."
	pytest app/scripts/test_mock.py -v


clean-mock-services:
	@echo "🧹 Cleaning mock service data..."
	rm -rf logs/mock_services/
	rm -rf data/mock_services/


dev-mock-services:
	@echo "🔧 Starting mock services in development mode..."
	python -m app.cli.mock_services start

# Check mock service status
status-mock-services:
	@echo "🔍 Checking mock service status..."
	python -m app.cli.mock_services status

# Generate test events
generate-test-events:
	@echo "🎯 Generating test events..."
	python -m app.cli.mock_services generate-events --count 20

# Run integration tests
test-integration:
	@echo "🔗 Running integration tests..."
	python -m app.cli.mock_services test

# Docker commands
docker-build-mock-services:
	@echo "🐳 Building mock services Docker image..."
	docker build -f Dockerfile.mock-services -t mock-services .

docker-start-mock-services:
	@echo "🐳 Starting mock services with Docker Compose..."
	docker-compose -f docker-compose.mock-services.yml up -d

docker-stop-mock-services:
	@echo "🐳 Stopping mock services Docker containers..."
	docker-compose -f docker-compose.mock-services.yml down

docker-logs-mock-services:
	@echo "📋 Showing mock services logs..."
	docker-compose -f docker-compose.mock-services.yml logs -f

# Development helpers
dev-setup: docker-build-mock-services
	@echo "✅ Mock services development environment ready"

dev-reset: docker-stop-mock-services clean-mock-services docker-start-mock-services
	@echo "🔄 Mock services environment reset"