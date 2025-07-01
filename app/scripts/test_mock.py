import asyncio
import pytest
import httpx
from typing import Dict, Any
import uuid
from datetime import datetime, timedelta

from app.mock.service_orchestrator import service_orchestrator
from app.mock.mock_services import MockServiceTester, WebhookPayloadGenerator
from app.mock.client import external_client

class TestMockServices:
    """Integration tests for mock external services"""
    
    @pytest.fixture(scope="class", autouse=True)
    async def setup_services(self):
        """Setup mock services for testing"""
        await service_orchestrator.start_services()
        # Wait for services to be ready
        await asyncio.sleep(3)
        yield
        await service_orchestrator.stop_services()
    
    @pytest.fixture
    def tenant_id(self):
        """Generate unique tenant ID for each test"""
        return f"test-tenant-{uuid.uuid4()}"
    
    async def test_user_management_service(self, tenant_id: str):
        """Test user management service CRUD operations"""
        # Test data
        user_data = {
            "email": "testuser@example.com",
            "name": "Test User",
            "tenant_id": tenant_id
        }
        
        # Create user
        created_user = await external_client.create_user(user_data)
        assert created_user is not None
        assert created_user["email"] == user_data["email"]
        assert created_user["tenant_id"] == tenant_id
        user_id = created_user["id"]
        
        # Get user
        retrieved_user = await external_client.get_user(user_id)
        assert retrieved_user is not None
        assert retrieved_user["id"] == user_id
        
        # Update user
        update_data = {**created_user, "name": "Updated Test User"}
        updated_user = await external_client.update_user(user_id, update_data)
        assert updated_user is not None
        assert updated_user["name"] == "Updated Test User"
        
        # Delete user
        delete_result = await external_client.delete_user(user_id)
        assert delete_result is not None
        
        # Verify deletion
        deleted_user = await external_client.get_user(user_id)
        assert deleted_user is None
    
    async def test_payment_service(self, tenant_id: str):
        """Test payment service operations"""
        # Create subscription
        subscription_data = {
            "tenant_id": tenant_id,
            "user_id": str(uuid.uuid4()),
            "plan_id": "premium",
            "status": "active",
            "amount": 29.99,
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        created_subscription = await external_client.create_subscription(subscription_data)
        assert created_subscription is not None
        assert created_subscription["tenant_id"] == tenant_id
        
        # Process payment
        payment_data = {
            "subscription_id": created_subscription["id"],
            "tenant_id": tenant_id,
            "amount": 29.99,
            "currency": "USD"
        }
        
        payment_result = await external_client.process_payment(payment_data)
        assert payment_result is not None
        assert payment_result["amount"] == 29.99
        assert payment_result["status"] in ["succeeded", "failed"]
    
    async def test_communication_service(self, tenant_id: str):
        """Test communication service operations"""
        notification_data = {
            "tenant_id": tenant_id,
            "user_id": str(uuid.uuid4()),
            "type": "email",
            "recipient": "test@example.com",
            "subject": "Test Notification",
            "content": "This is a test notification",
            "status": "pending"
        }
        
        sent_notification = await external_client.send_notification(notification_data)
        assert sent_notification is not None
        assert sent_notification["tenant_id"] == tenant_id
        assert sent_notification["status"] == "sent"
    
    async def test_service_health_checks(self):
        """Test health checks for all services"""
        health_results = await external_client.health_check_all()
        
        expected_services = ["user_management", "payment", "communication"]
        for service in expected_services:
            assert service in health_results
            assert health_results[service] is True
    
    async def test_webhook_generation(self, tenant_id: str):
        """Test webhook event generation"""
        generator = WebhookPayloadGenerator()
        
        # Test user event generation
        user_event = generator.generate_user_event(tenant_id, "USER_CREATED")
        assert user_event.tenant_id == tenant_id
        assert user_event.event_type == "USER_CREATED"
        assert "email" in user_event.data
        
        # Test payment event generation
        payment_event = generator.generate_payment_event(tenant_id, "PAYMENT_SUCCEEDED")
        assert payment_event.tenant_id == tenant_id
        assert payment_event.event_type == "PAYMENT_SUCCEEDED"
        assert "amount" in payment_event.data
        
        # Test notification event generation
        notification_event = generator.generate_notification_event(tenant_id, "EMAIL_DELIVERED")
        assert notification_event.tenant_id == tenant_id
        assert notification_event.event_type == "EMAIL_DELIVERED"
        assert "recipient" in notification_event.data
    
    async def test_concurrent_requests(self, tenant_id: str):
        """Test handling concurrent requests"""
        # Create multiple users concurrently
        tasks = []
        for i in range(10):
            user_data = {
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "tenant_id": tenant_id
            }
            task = external_client.create_user(user_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most requests succeeded
        successful_results = [r for r in results if not isinstance(r, Exception) and r is not None]
        assert len(successful_results) >= 8  # Allow some failures due to timing
