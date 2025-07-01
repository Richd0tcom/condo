# Condo - Enterprise Multi-Tenant SaaS Platform (In progress)

A comprehensive backend system that combines multi-tenant SaaS platform features with external API integration capabilities. This platform demonstrates advanced platform engineering and integration architecture skills.

## 🏗️ Architecture Overview

Orion is built as a modern, scalable SaaS platform with the following key architectural components:

- **Multi-Tenant Data Isolation**: Database-level security with tenant context middleware
- **JWT Authentication**: Role-based access control with secure token management
- **RESTful API**: FastAPI-based endpoints with comprehensive validation
- **External Integration**: Webhook processing with async event handling
- **Audit & Compliance**: Comprehensive logging for all data modifications
- **Circuit Breaker Pattern**: Resilient external API communication
- **Rate Limiting**: Enterprise-grade request throttling



## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Redis 6+
- Docker (optional, not necessary needed unless for testing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Richd0tcom/condo
   cd condo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup**
   ```bash
   # Run migrations
   alembic upgrade head
   ```

5. **Start Services**
   ```bash
   # Start Redis
   redis-server

   # Start Celery worker
   celery -A app.tasks.celery worker --loglevel=info

   # Start the application
   uvicorn app.main:app --reload
   ```

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/register` - Register new tenant with admin user
- `POST /api/v1/auth/login` - Authenticate and get JWT token
- `POST /api/v1/auth/logout` - Logout (client-side token invalidation)
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Tenant Management

- `GET /api/v1/tenants/` - List tenants (admin only)
- `POST /api/v1/tenants/` - Create new tenant
- `GET /api/v1/tenants/{tenant_id}` - Get tenant details
- `PUT /api/v1/tenants/{tenant_id}` - Update tenant
- `DELETE /api/v1/tenants/{tenant_id}` - Delete tenant

### User Management

- `GET /api/v1/users/` - List users (tenant-scoped)
- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Webhook Integration

- `POST /api/v1/webhooks/{service_name}` - Receive webhooks from external services
- `GET /api/v1/webhooks/health` - Webhook processing system health check

## 🔧 Core Components

### Multi-Tenancy Architecture

**Key Features:**
- Database-level tenant isolation with `tenant_id` foreign keys
- Middleware-based tenant context injection
- Automatic tenant filtering in all queries
- Subdomain-based tenant resolution

### Authentication & Authorization

**Security Features:**
- JWT tokens with configurable expiration
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Failed login attempt tracking
- Account lockout protection

### Webhook Processing Pipeline

**Integration Features:**
- Signature verification for webhook security
- Timestamp validation to prevent replay attacks
- Idempotency handling with hash-based deduplication
- Bulk webhook processing for high-throughput scenarios
- Dead letter queue for failed events

### Circuit Breaker Pattern

**Resilience Features:**
- Configurable failure thresholds
- Automatic recovery after timeout
- Half-open state for gradual recovery
- Per-service circuit breaker instances



## 🔍 Monitoring & Observability

### Health Checks

- `GET /health` - Overall system health
- `GET /api/v1/webhooks/health` - Webhook processing health
- Celery worker health monitoring

### Logging

- Structured logging with `structlog`
- JSON-formatted logs for easy parsing
- Tenant and user context in all log entries
- Audit trail for compliance requirements

### Metrics (comming soon)


## 🛡️ Security Features

### Data Protection

- Tenant data isolation at database level
- JWT token security with configurable expiration
- Password hashing with bcrypt
- Input validation and sanitization
- Rate limiting to prevent abuse

### Webhook Security

- HMAC signature verification
- Timestamp validation to prevent replay attacks
- Configurable secret keys per service
- Payload size limits

### API Security

- Request/response logging
- Error handling without information leakage
- Role-based access control

## 🚀 Deployment

### Docker Deployment (comming soon)




## 🧪 Testing (comming soon)


## 📈 Performance Considerations

### Optimization Strategies

- Database indexing on tenant_id columns
- Redis caching for frequently accessed data
- Connection pooling for database connections
- Async processing for webhook events




## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
