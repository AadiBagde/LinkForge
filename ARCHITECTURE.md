# System Architecture

## Overview

LinkForge is a scalable, production-ready URL shortening and analytics platform built with modern Python web technologies. This document describes the system architecture, design patterns, and implementation details.

---

## Architectural Layers

```
┌─────────────────────────────────────┐
│      FastAPI (HTTP Layer)           │  Request handling, routing, validation
├─────────────────────────────────────┤
│   Service Layer (Business Logic)    │  URL shortening, analytics, auth
├─────────────────────────────────────┤
│  Data Access Layer (SQLAlchemy)     │  Database abstraction and ORM
├─────────────────────────────────────┤
│    Cache Layer (Redis)              │  Performance optimization
├─────────────────────────────────────┤
│   Database Layer (PostgreSQL)       │  Persistent storage
└─────────────────────────────────────┘
```

---

## Components

### 1. Web Framework (FastAPI)

**Purpose:** HTTP request handling, routing, automatic API documentation

**Key Features:**
- ASGI async/await support for non-blocking I/O
- Automatic OpenAPI (Swagger) documentation
- Pydantic-based request validation
- Dependency injection system
- CORS support for cross-origin requests
- Background task support

**Key Files:**
- `app/main.py` – Application setup and router registration
- `app/core/error_handlers.py` – Global exception handlers
- `app/core/logging_config.py` – Request/response logging middleware

### 2. API Routes

**Authentication (`app/api/auth.py`)**
- `POST /auth/register` – User registration
- `POST /auth/login` – JWT token generation
- `GET /auth/me` – Get current user profile

**URL Shortening (`app/api/urls.py`)**
- `POST /shorten` – Create short URL
- `GET /{short_code}` – Redirect to original URL (tracks clicks)
- `GET /qr/{short_code}` – Generate QR code

**Analytics (`app/api/advanced_analytics.py`)**
- `GET /analytics/detailed/{short_code}` – Complete analytics
- `GET /analytics/daily/{short_code}` – Daily breakdown
- `GET /analytics/geography/{short_code}` – Geographic distribution
- `GET /analytics/devices/{short_code}` – Device breakdown
- `GET /analytics/referrers/{short_code}` – Top referrers
- `GET /analytics/top` – Top URLs

**URL Management (`app/api/url_management.py`)**
- `GET /urls/my-urls` – User's URLs with statistics
- `GET /urls/search` – Search user's URLs
- `PUT /urls/{short_code}` – Update URL
- `DELETE /urls/{short_code}` – Delete URL
- `POST /urls/bulk-create` – Create up to 100 URLs

### 3. Service Layer

Services implement business logic and are independent of HTTP framework:

**ShortenerService** (`app/services/shortener_service.py`)
- URL validation
- Short code generation (Base62)
- Custom code validation
- Uniqueness checking

**AuthService** (`app/services/auth_service.py`)
- User registration
- Password hashing (bcrypt)
- JWT token generation/validation
- User authentication

**CacheService** (`app/services/cache_service.py`)
- Redis connection management
- URL caching (TTL-based)
- Graceful degradation (falls back to database)

**AnalyticsService** (`app/services/analytics_service.py`)
- Click tracking
- URL performance metrics

**AdvancedAnalyticsService** (`app/services/advanced_analytics_service.py`)
- Daily breakdown aggregation
- Device/browser/OS statistics
- Geographic analysis
- Referrer extraction

**DeviceService** (`app/services/device_service.py`)
- User-Agent string parsing
- Device type detection
- Browser/OS identification

**RateLimitService** (`app/services/rate_limit_service.py`)
- Per-IP rate limiting
- Redis-backed distributed rate limiting
- Configurable limits and windows

---

## Data Models

### Database Schema

**Users Table**
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  username VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
```

**URLs Table**
```sql
CREATE TABLE urls (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  short_code VARCHAR UNIQUE NOT NULL,
  user_id INTEGER FOREIGN KEY,
  expires_at DATETIME,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
```

**Clicks Table**
```sql
CREATE TABLE clicks (
  id INTEGER PRIMARY KEY,
  url_id INTEGER FOREIGN KEY NOT NULL,
  ip_address VARCHAR,
  user_agent TEXT,
  referrer TEXT,
  country VARCHAR,
  city VARCHAR,
  browser VARCHAR,
  browser_version VARCHAR,
  os_name VARCHAR,
  os_version VARCHAR,
  device_type VARCHAR,
  clicked_at DATETIME DEFAULT NOW()
);
```

### Pydantic Models

Input validation schemas:

```python
class URLCreateRequest(BaseModel):
    original_url: str
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str  # Must meet strength requirements
```

Output schemas:

```python
class URLResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    url_id: int
    total_clicks: int
    daily_stats: List[DailyBreakdown]
    device_breakdown: Dict[str, int]
    # ... more fields
```

---

## Authentication & Security

### JWT Authentication Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /auth/register
       │ {email, username, password}
       ▼
┌──────────────────────────────────┐
│   FastAPI Endpoint               │
│  - Validate email format         │
│  - Check password strength       │
│  - Verify unique email/username  │
└──────────────────────┬───────────┘
                       │ CREATE USER
                       ▼
            ┌──────────────────┐
            │  Database        │
            │  Hash password   │
            │  Store user      │
            └────────┬─────────┘
                     │ CREATE TOKEN
                     ▼
            ┌──────────────────┐
            │  AuthService     │
            │  Generate JWT    │
            │  Expiry: 30min   │
            └────────┬─────────┘
                     │
                     ▼
            Response with token
```

### Security Features

- **Password Hashing:** bcrypt with 12 salt rounds
- **JWT Signing:** HS256 algorithm with secret key
- **Token Expiration:** 30 minutes (configurable)
- **CORS:** Configurable allowed origins
- **Input Validation:** All inputs validated with Pydantic
- **XSS Prevention:** HTML/JavaScript sanitization
- **SQL Injection Prevention:** ORM parameterized queries

---

## Caching Strategy

### Cache Layer Design

```
┌─────────────────────────┐
│  Request for URL        │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────┐
    │ Check Redis    │
    │ Cache Hit?     │
    └────┬───────┬───┘
         │ YES   │ NO
         │       ▼
         │   ┌─────────────┐
         │   │  Database   │
         │   │  Query      │
         │   └──────┬──────┘
         │          │
         │          ▼
         │   ┌──────────────┐
         │   │ Write Cache  │
         │   │ TTL: 3600s   │
         │   └──────┬───────┘
         │          │
         ▼          ▼
    ┌─────────────────┐
    │  Return Result  │
    └─────────────────┘
```

### Cache Configuration

- **TTL (Time To Live):** 3600 seconds (1 hour) for URLs
- **Fallback:** Automatic database fallback if Redis unavailable
- **Invalidation:** Cache cleared on URL update/delete
- **Key Format:** `url:{short_code}` for consistency

---

## Rate Limiting

### Rate Limit Implementation

```
┌──────────────┐
│  Request     │
└───────┬──────┘
        │
        ▼
┌──────────────────────────┐
│ Extract Client IP        │
│ (from X-Forwarded-For)   │
└───────┬──────────────────┘
        │
        ▼
┌──────────────────────────┐
│ Check Redis Counter      │
│ Key: ratelimit:{ip}      │
│ Window: 60 seconds       │
└───┬──────────────────┬───┘
    │ Under Limit      │ Over Limit
    │                  │
    ▼                  ▼
Accept Request   Return 429 (Too Many Requests)
Increment Counter
```

### Configuration

- **Default Limit:** 10 requests per minute per IP
- **Window:** 60 seconds
- **Headers:** Returns `X-RateLimit-Remaining` and `X-RateLimit-Reset`

---

## Analytics Pipeline

### Click Tracking Flow

```
┌──────────────────────┐
│ GET /{short_code}    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 1. Lookup URL        │
│ (Cache/Database)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 2. Check Expiration  │
│ If expired: 410 Gone │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 3. Log Click         │
│ (Background Task)    │
│ - IP address         │
│ - User-Agent         │
│ - Referrer           │
│ - Timestamp          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 4. Extract Location  │
│ (Async, non-blocking)│
│ IP → Country/City    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 5. Parse User-Agent  │
│ - Device type        │
│ - Browser/OS         │
│ - Bot detection      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 6. Store Click       │
│ (Database insert)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 307 Redirect         │
│ to original URL      │
└──────────────────────┘
```

### Analytics Aggregation

Aggregation functions compute statistics from clicks table:

```python
# Daily breakdown
SELECT DATE(clicked_at) as date, COUNT(*) as clicks
FROM clicks WHERE url_id = ?
GROUP BY DATE(clicked_at)

# Device distribution
SELECT device_type, COUNT(*) as clicks
FROM clicks WHERE url_id = ?
GROUP BY device_type

# Geographic analysis
SELECT country, city, COUNT(*) as clicks
FROM clicks WHERE url_id = ?
GROUP BY country, city
ORDER BY clicks DESC
```

---

## Error Handling

### Global Error Handler Middleware

```python
@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

### HTTP Status Codes

- **200 OK** – Successful request
- **201 Created** – Resource created
- **307 Redirect** – Redirect to original URL
- **400 Bad Request** – Invalid input
- **401 Unauthorized** – Missing/invalid token
- **404 Not Found** – Resource not found
- **409 Conflict** – Duplicate short code
- **410 Gone** – URL expired
- **429 Too Many Requests** – Rate limited
- **500 Internal Server Error** – Server error

---

## Deployment Architecture

### Production Stack

```
┌──────────────────────────────────┐
│  Client Browser / API Client     │
└────────────────┬─────────────────┘
                 │ HTTPS
                 ▼
        ┌────────────────┐
        │ Render.com     │  Load balancing, auto-scaling
        │ Web Service    │  Health checks, monitoring
        └────────┬───────┘
                 │
         ┌───────┴─────────┬──────────────┐
         │                 │              │
         ▼                 ▼              ▼
    ┌─────────┐     ┌──────────┐   ┌──────────┐
    │FastAPI  │     │ Neon     │   │ Upstash  │
    │Instance │────▶│PostgreSQL│   │  Redis   │
    └─────────┘     └──────────┘   └──────────┘
         │
         └─▶ Monitoring: Render Logs
         └─▶ Alerts: Email notifications
```

### Scaling Strategy

1. **Horizontal Scaling:** Add more FastAPI instances
2. **Database Scaling:** Neon auto-scaling PostgreSQL
3. **Cache Scaling:** Upstash Redis with automatic failover
4. **Load Balancing:** Render's built-in load balancer

---

## Development Workflow

### Local Development

```
Development Machine
├── Python Virtual Environment
├── FastAPI (uvicorn)
├── Docker Compose
│   ├── PostgreSQL (or MySQL)
│   └── Redis
└── pytest (testing)
```

### CI/CD Pipeline

```
┌─────────────────┐
│  Git Push       │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────┐
│ GitHub Actions Workflow      │
├──────────────────────────────┤
│ 1. Run Tests (pytest)        │
│ 2. Lint Code (flake8, black) │
│ 3. Type Check (mypy)         │
│ 4. Security Scan (bandit)    │
│ 5. Build Docker Image        │
│ 6. Push to Registry          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Render.com           │
│ - Pull Docker image  │
│ - Deploy services    │
│ - Run health checks  │
│ - Monitor uptime     │
└──────────────────────┘
```

---

## Performance Optimization

### Query Optimization

- **Indexes:** On `short_code`, `user_id`, `created_at`, `expires_at`
- **Eager Loading:** Use SQLAlchemy relationships strategically
- **Pagination:** Limit results to 50 URLs per page
- **Aggregation:** Use database GROUP BY for statistics

### Caching Strategy

- **Cache Hits:** ~90% for frequently accessed URLs
- **Cache Invalidation:** Immediate on URL updates
- **Graceful Degradation:** Fall back to database if Redis down

### Connection Pooling

```python
# Development: 5 connections, max overflow 10
# Production: 20 connections, max overflow 40
SQLAlchemy QueuePool configuration
```

### Response Times

- **Redirect (cache hit):** <50ms
- **Analytics query:** <100ms
- **URL creation:** <200ms
- **Bulk create (100 URLs):** <1s

---

## Database Migrations

Using Alembic for version-controlled schema changes:

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Monitoring & Observability

### Logging

- **Format:** Structured JSON for machine parsing
- **Level:** INFO in production, DEBUG in development
- **Context:** Request ID, user ID, IP address
- **Storage:** File-based with rotation

### Health Check

```bash
GET /health
{
  "status": "healthy",
  "timestamp": "2026-07-01T12:00:00Z"
}
```

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [JWT Specification](https://tools.ietf.org/html/rfc7519)
