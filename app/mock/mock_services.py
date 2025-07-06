import asyncio
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
import json
from contextlib import asynccontextmanager

# Mock Service Models
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"

class NotificationStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"

# Webhook Event Types
class WebhookEventType(str, Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    EMAIL_SENT = "email.sent"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_FAILED = "email.failed"

# Request/Response Models
class MockUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MockSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    amount: float
    currency: str = "USD"
    billing_cycle: str = "monthly"
    current_period_start: datetime
    current_period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MockNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    type: str  # email, sms, push
    recipient: str
    subject: Optional[str] = None
    content: str
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: WebhookEventType
    tenant_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None

# Webhook Configuration
@dataclass
class WebhookConfig:
    url: str
    secret: str
    events: List[WebhookEventType]
    active: bool = True

# Mock Service Registry
class MockServiceRegistry:
    def __init__(self):
        self.webhooks: Dict[str, List[WebhookConfig]] = {}
        self.users: Dict[str, MockUser] = {}
        self.subscriptions: Dict[str, MockSubscription] = {}
        self.notifications: Dict[str, MockNotification] = {}
        
    def register_webhook(self, service_name: str, config: WebhookConfig):
        """Register webhook endpoint for a service"""
        if service_name not in self.webhooks:
            self.webhooks[service_name] = []
        self.webhooks[service_name].append(config)
        
    async def send_webhook(self, service_name: str, event: WebhookEvent):
        """Send webhook to registered endpoints"""
        if service_name not in self.webhooks:
            return

        print("I rannnnnnnnnnnn")
            
        for webhook_config in self.webhooks[service_name]:
            if not webhook_config.active or event.event_type not in webhook_config.events:
                continue
                
            try:
                # Add signature for webhook verification
                payload = event.model_dump(mode='json')
                signature = self._generate_signature(json.dumps(payload, sort_keys=True), webhook_config.secret)
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Event-Type": event.event_type,
                    "X-Event-ID": event.id
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_config.url,
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )
                    print("eventoooo", event)
                    
                    if response.status_code != 200:
                        print(f"Webhook failed for {webhook_config.url}: {response.status_code}")
                        
            except Exception as e:
                print(f"Webhook error for {webhook_config.url}: {str(e)}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook verification"""
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"

# Global service registry
service_registry = MockServiceRegistry()

# User Management Service
class MockUserManagementService:
    def __init__(self, registry: MockServiceRegistry):
        self.registry = registry
        self.app = FastAPI(title="Mock User Management Service", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/users", response_model=MockUser)
        async def create_user(user_data: MockUser, background_tasks: BackgroundTasks):
            # Simulate processing delay
            await asyncio.sleep(random.uniform(1, 5))
            
            self.registry.users[user_data.id] = user_data
            
            # Send webhook
            event = WebhookEvent(
                event_type=WebhookEventType.USER_CREATED,
                tenant_id=user_data.tenant_id,
                data=user_data.model_dump(mode='json')
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "user_management", event
            )
            
            return user_data
        
        @self.app.get("/users/{user_id}", response_model=MockUser)
        async def get_user(user_id: str):
            if user_id not in self.registry.users:
                raise HTTPException(status_code=404, detail="User not found")
            return self.registry.users[user_id]
        
        @self.app.put("/users/{user_id}", response_model=MockUser)
        async def update_user(user_id: str, user_data: MockUser, background_tasks: BackgroundTasks):
            if user_id not in self.registry.users:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Simulate processing delay
            await asyncio.sleep(random.uniform(1, 5))
            
            user_data.updated_at = datetime.utcnow()
            self.registry.users[user_id] = user_data
            
            # Send webhook
            event = WebhookEvent(
                event_type=WebhookEventType.USER_UPDATED,
                tenant_id=user_data.tenant_id,
                data=user_data.model_dump(mode='json')
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "user_management", event
            )
            
            return user_data
        
        @self.app.delete("/users/{user_id}")
        async def delete_user(user_id: str, background_tasks: BackgroundTasks):
            if user_id not in self.registry.users:
                raise HTTPException(status_code=404, detail="User not found")
            
            user = self.registry.users[user_id]
            del self.registry.users[user_id]
            
            # Send webhook
            event = WebhookEvent(
                event_type=WebhookEventType.USER_DELETED,
                tenant_id=user.tenant_id,
                data={"id": user_id, "tenant_id": user.tenant_id}
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "user_management", event
            )
            
            return {"message": "User deleted successfully"}
        
        @self.app.get("/users", response_model=List[MockUser])
        async def list_users(tenant_id: Optional[str] = None, limit: int = 100):
            users = list(self.registry.users.values())
            if tenant_id:
                users = [u for u in users if u.tenant_id == tenant_id]
            return users[:limit]

# Payment Service
class MockPaymentService:
    def __init__(self, registry: MockServiceRegistry):
        self.registry = registry
        self.app = FastAPI(title="Mock Payment Service", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/subscriptions", response_model=MockSubscription)
        async def create_subscription(sub_data: MockSubscription, background_tasks: BackgroundTasks):
            # Simulate processing delay
            await asyncio.sleep(random.uniform(0.2, 0.8))
            
            self.registry.subscriptions[sub_data.id] = sub_data
            
            # Send webhook
            event = WebhookEvent(
                event_type=WebhookEventType.SUBSCRIPTION_CREATED,
                tenant_id=sub_data.tenant_id,
                data=sub_data.model_dump(mode='json')
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "payment_service", event
            )
            
            return sub_data
        
        @self.app.get("/subscriptions/{subscription_id}", response_model=MockSubscription)
        async def get_subscription(subscription_id: str):
            if subscription_id not in self.registry.subscriptions:
                raise HTTPException(status_code=404, detail="Subscription not found")
            return self.registry.subscriptions[subscription_id]
        
        @self.app.post("/payments/process")
        async def process_payment(payment_data: Dict[str, Any], background_tasks: BackgroundTasks):
            # Simulate payment processing
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Random success/failure for testing
            success = random.random() > 0.2  # 80% success rate
            
            event_type = WebhookEventType.PAYMENT_SUCCEEDED if success else WebhookEventType.PAYMENT_FAILED
            
            result = {
                "id": str(uuid.uuid4()),
                "subscription_id": payment_data.get("subscription_id"),
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency", "USD"),
                "status": "succeeded" if success else "failed",
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Send webhook
            event = WebhookEvent(
                event_type=event_type,
                tenant_id=payment_data.get("tenant_id"),
                data=result
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "payment_service", event
            )
            
            return result
        
        @self.app.post("/subscriptions/{subscription_id}/update")
        async def update_subscription(subscription_id: str, update_data: Dict[str, Any], background_tasks: BackgroundTasks):
            if subscription_id not in self.registry.subscriptions:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            subscription = self.registry.subscriptions[subscription_id]
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            
            self.registry.subscriptions[subscription_id] = subscription
            
            # Send webhook
            event = WebhookEvent(
                event_type=WebhookEventType.SUBSCRIPTION_UPDATED,
                tenant_id=subscription.tenant_id,
                data=subscription.model_dump(mode='json')
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "payment_service", event
            )
            
            return subscription

# Communication Service
class MockCommunicationService:
    def __init__(self, registry: MockServiceRegistry):
        self.registry = registry
        self.app = FastAPI(title="Mock Communication Service", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/notifications/send", response_model=MockNotification)
        async def send_notification(notification: MockNotification, background_tasks: BackgroundTasks):
            # Simulate sending delay
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Random delivery success/failure
            delivery_success = random.random() > 0.1  # 90% success rate
            
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            self.registry.notifications[notification.id] = notification
            
            # Send initial webhook
            event = WebhookEvent(
                event_type=WebhookEventType.EMAIL_SENT,
                tenant_id=notification.tenant_id,
                data=notification.model_dump(mode='json')
            )
            
            background_tasks.add_task(
                self.registry.send_webhook, "communication_service", event
            )
            
            # Schedule delivery status update
            background_tasks.add_task(
                self._simulate_delivery, notification.id, delivery_success
            )
            
            return notification
        
        @self.app.get("/notifications/{notification_id}", response_model=MockNotification)
        async def get_notification(notification_id: str):
            if notification_id not in self.registry.notifications:
                raise HTTPException(status_code=404, detail="Notification not found")
            return self.registry.notifications[notification_id]
        
        @self.app.get("/notifications", response_model=List[MockNotification])
        async def list_notifications(tenant_id: Optional[str] = None, limit: int = 100):
            notifications = list(self.registry.notifications.values())
            if tenant_id:
                notifications = [n for n in notifications if n.tenant_id == tenant_id]
            return notifications[:limit]
    
    async def _simulate_delivery(self, notification_id: str, success: bool):
        """Simulate email delivery with delay"""
        # Wait for delivery simulation
        await asyncio.sleep(random.uniform(2.0, 10.0))
        
        notification = self.registry.notifications.get(notification_id)
        if not notification:
            return
        
        if success:
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
            event_type = WebhookEventType.EMAIL_DELIVERED
        else:
            notification.status = NotificationStatus.FAILED
            event_type = WebhookEventType.EMAIL_FAILED
        
        self.registry.notifications[notification_id] = notification
        
        # Send delivery status webhook
        event = WebhookEvent(
            event_type=event_type,
            tenant_id=notification.tenant_id,
            data=notification.dict()
        )
        
        await self.registry.send_webhook("communication_service", event)

# Service Discovery and Configuration
class MockServiceDiscovery:
    def __init__(self):
        self.services = {
            "user_management": {
                "url": "http://localhost:8001",
                "health_endpoint": "/health",
                "version": "1.0.0"
            },
            "payment": {
                "url": "http://localhost:8002", 
                "health_endpoint": "/health",
                "version": "1.0.0"
            },
            "communication": {
                "url": "http://localhost:8003",
                "health_endpoint": "/health", 
                "version": "1.0.0"
            }
        }
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL by name"""
        service = self.services.get(service_name)
        return service["url"] if service else None
    
    async def health_check(self, service_name: str) -> bool:
        """Check service health"""
        service = self.services.get(service_name)
        if not service:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{service['url']}{service['health_endpoint']}",
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        for service_name in self.services.keys():
            results[service_name] = await self.health_check(service_name)
        return results

# Webhook Payload Generators for Testing
class WebhookPayloadGenerator:
    @staticmethod
    def generate_user_event(tenant_id: str, event_type: WebhookEventType) -> WebhookEvent:
        """Generate user-related webhook events"""
        user_data = {
            "id": str(uuid.uuid4()),
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "name": f"Test User {random.randint(1, 100)}",
            "status": random.choice(list(UserStatus)),
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return WebhookEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            data=user_data
        )
    
    @staticmethod
    def generate_payment_event(tenant_id: str, event_type: WebhookEventType) -> WebhookEvent:
        """Generate payment-related webhook events"""
        payment_data = {
            "id": str(uuid.uuid4()),
            "subscription_id": str(uuid.uuid4()),
            "amount": round(random.uniform(10.0, 500.0), 2),
            "currency": "USD",
            "status": "succeeded" if event_type == WebhookEventType.PAYMENT_SUCCEEDED else "failed",
            "processed_at": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id
        }
        
        return WebhookEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            data=payment_data
        )
    
    @staticmethod
    def generate_notification_event(tenant_id: str, event_type: WebhookEventType) -> WebhookEvent:
        """Generate notification-related webhook events"""
        notification_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": str(uuid.uuid4()),
            "type": "email",
            "recipient": f"user{random.randint(1000, 9999)}@example.com",
            "subject": "Test Notification",
            "content": "This is a test notification",
            "status": "delivered" if event_type == WebhookEventType.EMAIL_DELIVERED else "failed",
            "sent_at": datetime.utcnow().isoformat(),
            "delivered_at": datetime.utcnow().isoformat() if event_type == WebhookEventType.EMAIL_DELIVERED else None
        }
        
        return WebhookEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            data=notification_data
        )


class MockServiceTester:
    def __init__(self, service_discovery: MockServiceDiscovery):
        self.service_discovery = service_discovery
    
    async def test_user_service_integration(self, tenant_id: str):
        """Test complete user service integration"""
        service_url = self.service_discovery.get_service_url("user_management")
        
        
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "tenant_id": tenant_id
        }
        
        async with httpx.AsyncClient() as client:
            # Create
            response = await client.post(f"{service_url}/users", json=user_data)
            assert response.status_code == 200
            user = response.json()
            
            # Read
            response = await client.get(f"{service_url}/users/{user['id']}")
            assert response.status_code == 200
            
            # Update
            user["name"] = "Updated Name"
            response = await client.put(f"{service_url}/users/{user['id']}", json=user)
            assert response.status_code == 200
            
            # Delete
            response = await client.delete(f"{service_url}/users/{user['id']}")
            assert response.status_code == 200
            
        return True
    
    async def test_payment_service_integration(self, tenant_id: str):
        """Test payment service integration"""
        service_url = self.service_discovery.get_service_url("payment")
        
        subscription_data = {
            "tenant_id": tenant_id,
            "user_id": str(uuid.uuid4()),
            "plan_id": "premium",
            "status": "active",
            "amount": 29.99,
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            # Create subscription
            response = await client.post(f"{service_url}/subscriptions", json=subscription_data)
            assert response.status_code == 200
            subscription = response.json()
            
            # Process payment
            payment_data = {
                "subscription_id": subscription["id"],
                "tenant_id": tenant_id,
                "amount": 29.99,
                "currency": "USD"
            }
            
            response = await client.post(f"{service_url}/payments/process", json=payment_data)
            assert response.status_code == 200
            
        return True
    
    async def test_communication_service_integration(self, tenant_id: str):
        """Test communication service integration"""
        service_url = self.service_discovery.get_service_url("communication")
        
        notification_data = {
            "tenant_id": tenant_id,
            "user_id": str(uuid.uuid4()),
            "type": "email",
            "recipient": "test@example.com",
            "subject": "Test Email",
            "content": "This is a test email",
            "status": "pending"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{service_url}/notifications/send", json=notification_data)
            assert response.status_code == 200
            
        return True