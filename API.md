# API Reference

Complete reference for all LinkForge API endpoints with examples.

---

## Base URL

```
http://localhost:8000  # Development
https://linkforge.example.com  # Production
```

## Authentication

All protected endpoints require JWT Bearer token:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Authentication Endpoints

### Register User

**Request:**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "is_active": true,
    "created_at": "2026-07-01T10:30:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access_token_type": "bearer"
}
```

**Error (400):**
```json
{
  "detail": "Email already registered"
}
```

---

### Login

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access_token_type": "bearer"
}
```

**Error (401):**
```json
{
  "detail": "Invalid email or password"
}
```

---

### Get Current User

**Request:**
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2026-07-01T10:30:00Z"
}
```

**Error (401):**
```json
{
  "detail": "Not authenticated"
}
```

---

## URL Shortening Endpoints

### Create Short URL

**Request:**
```http
POST /shorten
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "original_url": "https://github.com/AadiBagde/LinkForge",
  "custom_code": "linkforge",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Response (200 OK):**
```json
{
  "short_url": "http://localhost:8000/linkforge",
  "short_code": "linkforge",
  "original_url": "https://github.com/AadiBagde/LinkForge",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Error (409):**
```json
{
  "detail": "Short code 'linkforge' already exists"
}
```

---

### Redirect to Original URL

**Request:**
```http
GET /abc123
```

**Response (307 Temporary Redirect):**
```
Location: https://github.com/AadiBagde/LinkForge
```

The request is logged with:
- IP address
- User-Agent
- Referrer
- Country/City (if available)
- Device type
- Browser/OS information

**Error (404):**
```json
{
  "detail": "Short code not found"
}
```

**Error (410):**
```json
{
  "detail": "This URL has expired"
}
```

---

### Generate QR Code

**Request:**
```http
GET /qr/abc123
```

**Response (200 OK):**
```
Content-Type: image/png

[PNG image data]
```

---

## Analytics Endpoints

### Get Detailed Analytics

**Request:**
```http
GET /analytics/detailed/abc123?days=30
```

**Response (200 OK):**
```json
{
  "url_id": 1,
  "short_code": "abc123",
  "total_clicks": 156,
  "daily_stats": [
    {
      "date": "2026-06-01",
      "clicks": 10
    },
    {
      "date": "2026-06-02",
      "clicks": 15
    }
  ],
  "device_breakdown": {
    "Mobile": 78,
    "Desktop": 70,
    "Tablet": 8
  },
  "os_breakdown": {
    "Windows": 80,
    "iOS": 40,
    "Android": 30,
    "macOS": 6
  },
  "browser_breakdown": {
    "Chrome": 90,
    "Safari": 40,
    "Firefox": 20,
    "Edge": 6
  },
  "geography": [
    {
      "country": "United States",
      "city": "New York",
      "clicks": 50
    },
    {
      "country": "United States",
      "city": "San Francisco",
      "clicks": 30
    },
    {
      "country": "Canada",
      "city": "Toronto",
      "clicks": 20
    }
  ],
  "top_referrers": [
    {
      "referrer": "twitter.com",
      "clicks": 40
    },
    {
      "referrer": "reddit.com",
      "clicks": 20
    },
    {
      "referrer": "linkedin.com",
      "clicks": 15
    }
  ]
}
```

---

### Get Daily Breakdown

**Request:**
```http
GET /analytics/daily/abc123?days=30
```

**Response (200 OK):**
```json
[
  {
    "date": "2026-06-01",
    "clicks": 10
  },
  {
    "date": "2026-06-02",
    "clicks": 15
  },
  {
    "date": "2026-06-03",
    "clicks": 12
  }
]
```

**Parameters:**
- `days` (optional): Number of days (1-365, default 30)

---

### Get Geographic Data

**Request:**
```http
GET /analytics/geography/abc123
```

**Response (200 OK):**
```json
[
  {
    "country": "United States",
    "city": "New York",
    "clicks": 50
  },
  {
    "country": "United States",
    "city": "San Francisco",
    "clicks": 30
  },
  {
    "country": "Canada",
    "city": "Toronto",
    "clicks": 20
  }
]
```

---

### Get Device Distribution

**Request:**
```http
GET /analytics/devices/abc123
```

**Response (200 OK):**
```json
{
  "Mobile": 78,
  "Desktop": 70,
  "Tablet": 8
}
```

---

### Get Top Referrers

**Request:**
```http
GET /analytics/referrers/abc123?limit=10
```

**Response (200 OK):**
```json
[
  {
    "referrer": "twitter.com",
    "clicks": 40
  },
  {
    "referrer": "reddit.com",
    "clicks": 20
  },
  {
    "referrer": "linkedin.com",
    "clicks": 15
  }
]
```

**Parameters:**
- `limit` (optional): Max referrers to return (default 10)

---

### Get Top URLs

**Request:**
```http
GET /analytics/top?limit=10
```

**Response (200 OK):**
```json
[
  {
    "short_code": "github",
    "original_url": "https://github.com/AadiBagde/LinkForge",
    "clicks": 500
  },
  {
    "short_code": "portfolio",
    "original_url": "https://aadibagde.com",
    "clicks": 350
  },
  {
    "short_code": "twitter",
    "original_url": "https://twitter.com/aadibagde",
    "clicks": 280
  }
]
```

**Parameters:**
- `limit` (optional): Max URLs to return (default 10)

---

## URL Management Endpoints

### Get User's URLs

**Request:**
```http
GET /urls/my-urls?limit=50&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "total_urls": 5,
  "total_clicks": 1500,
  "active_urls": 4,
  "urls": [
    {
      "id": 1,
      "original_url": "https://github.com",
      "short_code": "github",
      "clicks": 500,
      "created_at": "2026-07-01T10:30:00Z",
      "expires_at": null,
      "is_expired": false
    },
    {
      "id": 2,
      "original_url": "https://aadibagde.com",
      "short_code": "portfolio",
      "clicks": 350,
      "created_at": "2026-06-15T14:20:00Z",
      "expires_at": "2026-12-31T23:59:59Z",
      "is_expired": false
    }
  ]
}
```

**Parameters:**
- `limit` (optional): Results per page (default 50, max 100)
- `offset` (optional): Pagination offset (default 0)

---

### Search URLs

**Request:**
```http
GET /urls/search?q=github&limit=20&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "total": 2,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "short_code": "github",
      "original_url": "https://github.com",
      "clicks": 500
    }
  ]
}
```

**Parameters:**
- `q` (required): Search query (searches short_code and original_url)
- `limit` (optional): Results per page (default 20)
- `offset` (optional): Pagination offset (default 0)

---

### Update URL

**Request:**
```http
PUT /urls/github
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "original_url": "https://github.com/AadiBagde",
  "custom_code": "gh",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "URL updated successfully",
  "short_code": "gh",
  "original_url": "https://github.com/AadiBagde",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**Error (404):**
```json
{
  "detail": "URL not found"
}
```

---

### Delete URL

**Request:**
```http
DELETE /urls/github
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "URL deleted successfully",
  "short_code": "github",
  "clicks_archived": 500
}
```

---

### Bulk Create URLs

**Request:**
```http
POST /urls/bulk-create
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "urls": [
    "https://github.com",
    "https://google.com",
    "https://stackoverflow.com"
  ],
  "custom_codes": ["gh", "google", "so"]
}
```

**Response (200 OK):**
```json
{
  "created": 3,
  "failed": 0,
  "urls": [
    {
      "original_url": "https://github.com",
      "short_code": "gh",
      "short_url": "http://localhost:8000/gh"
    },
    {
      "original_url": "https://google.com",
      "short_code": "google",
      "short_url": "http://localhost:8000/google"
    },
    {
      "original_url": "https://stackoverflow.com",
      "short_code": "so",
      "short_url": "http://localhost:8000/so"
    }
  ]
}
```

**Parameters:**
- `urls` (required): List of URLs to shorten (max 100)
- `custom_codes` (optional): List of custom codes (must match urls length)

---

## Error Responses

### Common Error Codes

**400 Bad Request**
```json
{
  "detail": "Invalid URL format"
}
```

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**409 Conflict**
```json
{
  "detail": "Short code already exists"
}
```

**410 Gone**
```json
{
  "detail": "URL has expired"
}
```

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Please try again in 60 seconds."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

All endpoints are rate limited:

- **Default:** 10 requests per minute per IP address
- **Headers:**
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

Example response header:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1656000000
```

---

## Pagination

Endpoints supporting pagination:
- `GET /urls/my-urls`
- `GET /urls/search`

**Parameters:**
- `limit` (optional): Results per page
- `offset` (optional): Pagination offset

**Response Format:**
```json
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "results": [...]
}
```

---

## Interactive Documentation

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

## Code Examples

### Python (requests)

```python
import requests

# Register
resp = requests.post("http://localhost:8000/auth/register", json={
    "email": "user@example.com",
    "username": "user",
    "password": "SecurePass123!"
})
token = resp.json()["access_token"]

# Create short URL
resp = requests.post(
    "http://localhost:8000/shorten",
    json={
        "original_url": "https://github.com",
        "custom_code": "gh"
    },
    headers={"Authorization": f"Bearer {token}"}
)
short_url = resp.json()["short_url"]

# Get analytics
resp = requests.get(
    f"http://localhost:8000/analytics/detailed/gh",
    headers={"Authorization": f"Bearer {token}"}
)
analytics = resp.json()
```

### JavaScript (fetch)

```javascript
// Login
const loginRes = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "SecurePass123!"
  })
});
const { access_token } = await loginRes.json();

// Create short URL
const shortRes = await fetch("http://localhost:8000/shorten", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${access_token}`
  },
  body: JSON.stringify({
    original_url: "https://github.com"
  })
});
const { short_url } = await shortRes.json();
console.log(short_url);
```

### cURL

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "SecurePass123!"
  }'

# Create short URL
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "original_url": "https://github.com",
    "custom_code": "gh"
  }'

# Get analytics
curl -X GET http://localhost:8000/analytics/detailed/gh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Changelog

### Version 1.0.0 (Current)
- Complete API implementation
- JWT authentication
- URL shortening and redirection
- Comprehensive analytics
- User management
- Rate limiting
- Caching
- Docker support
