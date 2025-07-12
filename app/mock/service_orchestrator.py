import asyncio
import structlog
import uvicorn
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from typing import Dict, List, Any
import logging

from app.models.webhooks import EventType

from .mock_services import (
    MockUserManagementService,
    MockPaymentService, 
    MockCommunicationService,
    MockServiceRegistry,
    MockServiceDiscovery,
    WebhookConfig
)

logger = structlog.get_logger(__name__)

class ServiceOrchestrator:
    """Orchestrates all mock external services"""
    
    def __init__(self):
        self.registry = MockServiceRegistry()
        self.discovery = MockServiceDiscovery()
        self.services: Dict[str, Any] = {}
        self.service_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
    def setup_services(self):
        """Initialize all mock services"""
        # Create service instances
        self.services = {
            "user_management": MockUserManagementService(self.registry),
            "payment": MockPaymentService(self.registry),
            "communication": MockCommunicationService(self.registry)
        }
        
        # Add health check endpoints to all services
        for service_name, service in self.services.items():
            print("healthy service: ", service_name)
            @service.app.get("/health")
            async def health_check(service_name: str = service_name):
                return {"status": "healthy", "service": service_name}
                
        logger.info("Mock services initialized")
    
    def register_webhooks(self, main_service_url: str = "http://localhost:8000/api/v1"):
        """Register webhook endpoints with mock services"""
        webhook_configs = {
            "user_management": WebhookConfig(
                url=f"{main_service_url}/webhooks/user_management",
                secret="user_webhook_secret_key",
                events=[
                    EventType.USER_CREATED,
                    EventType.USER_UPDATED,
                    EventType.USER_DELETED
                ]
            ),
            "payment_service": WebhookConfig(
                url=f"{main_service_url}/webhooks/payment_service",
                secret="payment_webhook_secret_key",
                events=[
                    EventType.SUBSCRIPTION_CREATED,
                    EventType.SUBSCRIPTION_UPDATED,
                    EventType.PAYMENT_SUCCESS,
                    EventType.PAYMENT_FAILED
                ]
            ),
            "communication_service": WebhookConfig(
                url=f"{main_service_url}/webhooks/communication_service",
                secret="comm_webhook_secret_key",
                events=[
                    EventType.EMAIL_BOUNCED,
                    EventType.EMAIL_DELIVERED,
                    EventType.EMAIL_FAILED
                ]
            )
        }
        
        for service_name, config in webhook_configs.items():
            self.registry.register_webhook(service_name, config)
            
        logger.info("Webhook configurations registered")
    
    async def start_services(self):
        """Start all mock services on different ports"""
        if self.running:
            return
            
        self.setup_services()
        self.register_webhooks()
        
        service_configs = [
            ("user_management", 8001),
            ("payment", 8002),
            ("communication", 8003)
        ]
        
        for service_name, port in service_configs:
            thread = threading.Thread(
                target=self._run_service,
                args=(service_name, port),
                daemon=True
            )
            thread.start()
            self.service_threads[service_name] = thread
            
        self.running = True
        
        # Wait a bit for services to start
        await asyncio.sleep(2)
        
        # Verify all services are healthy
        health_status = await self.discovery.health_check_all()
        for service_name, is_healthy in health_status.items():
            if is_healthy:
                logger.info(f"✅ {service_name} service is healthy")
            else:
                logger.error(f"❌ {service_name} service failed to start")
                
        logger.info("All mock services started")
    
    def _run_service(self, service_name: str, port: int):
        """Run individual service in thread"""
        try:
            service = self.services[service_name]
            uvicorn.run(
                service.app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"Failed to start {service_name} service: {e}")
    
    async def stop_services(self):
        """Stop all running services"""
        if not self.running:
            return
            
        # Note: In a real implementation, we'd need proper service shutdown
        # For now, we'll just mark as not running
        self.running = False
        logger.info("Mock services stopped")
    
    def get_service_registry(self) -> MockServiceRegistry:
        """Get the service registry for direct access"""
        return self.registry
    
    def get_service_discovery(self) -> MockServiceDiscovery:
        """Get service discovery for URL resolution"""
        return self.discovery
    
    async def health_check(self):
        health_status = await self.discovery.health_check_all()
        for service_name, is_healthy in health_status.items():
            if is_healthy:
                logger.info(f"✅ {service_name} service is healthy")
            else:
                logger.error(f"❌ {service_name} service failed to start")

service_orchestrator = ServiceOrchestrator()