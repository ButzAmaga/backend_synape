# Production API Steering Rules

## Purpose

All APIs must be designed and implemented as production-ready systems, not merely as endpoints that successfully return data.

The API should prioritize:

- Security
- Reliability
- Maintainability
- Predictability
- Observability
- Scalability
- Backward compatibility
- Clear separation of responsibilities

---

## Core API Pattern

Follow this high-level flow:

```text
Contract
  ↓
Authentication
  ↓
Validation
  ↓
Authorization
  ↓
Use Case / Business Logic
  ↓
Persistence / External Services
  ↓
Response
  ↓
Observability
```

Do not bypass these layers without a documented reason.

---

## API Contract

Every endpoint must have a clearly defined:

- HTTP method
- URL/path
- Authentication requirement
- Authorization requirement
- Request parameters
- Request body
- Response schema
- Error schema
- HTTP status codes

Use API versioning when breaking changes are expected.

Example:

```text
/api/v1/users
```

Prefer backward-compatible changes. Follow:

> Add before removing.

---

## Authentication and Authorization

Always distinguish:

**Authentication**

> Who is the caller?

**Authorization**

> Is the caller allowed to perform this operation on this resource?

A valid authentication token does not automatically grant access to every resource.

Resource ownership and permissions must be checked where applicable.

---

## Input Validation

Treat all client input as untrusted.

Validate at the API boundary before business logic executes.

Validate:

- Types
- Required fields
- String lengths
- Numeric ranges
- Enumerations
- Dates
- Nested objects
- Query parameters
- Path parameters
- Request sizes
- Uploaded files

Use a schema validation system such as Zod where appropriate.

---

## HTTP Semantics

Use HTTP status codes according to their meaning.

```text
200 OK
201 Created
204 No Content

400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Content
429 Too Many Requests

500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
```

Do not return `200 OK` for every outcome.

---

## Standard Error Format

Use a consistent error structure across the API.

Example:

```json
{
  "error": {
    "code": "INVALID_EMAIL",
    "message": "The email address is invalid.",
    "requestId": "req_123"
  }
}
```

Error responses should be predictable for frontend and API consumers.

Never expose:

- Stack traces
- Secrets
- API keys
- Database credentials
- Internal implementation details

---

## Layered Architecture

Keep HTTP concerns separate from business logic.

Preferred structure:

```text
API Gateway
    ↓
HTTP Handler / Controller
    ↓
Validation
    ↓
Authorization
    ↓
Use Case / Service
    ↓
Repository
    ↓
Database / External Service
```

The HTTP handler should not contain the entire application's business logic.

---

## Database Boundary

Never expose the database directly to clients.

Preferred:

```text
Client
  ↓
API
  ↓
Business Logic
  ↓
Repository
  ↓
Database
```

Do not automatically return complete database documents.

Explicitly define API response models and expose only required fields.

---

## Security

Follow least privilege.

AWS resources must receive only the permissions they require.

Never use broad permissions such as:

```text
*
```

when a specific permission is sufficient.

Never hard-code secrets in source code.

Use appropriate secret/configuration management such as:

- AWS Secrets Manager
- Environment variables for non-secret configuration
- IAM roles
- Appropriate credential providers

---

## Rate Limiting and Resource Protection

Protect expensive or abuse-prone endpoints.

Especially protect workflows involving:

- LLM inference
- External APIs
- File processing
- Expensive database operations
- Long-running jobs

Use appropriate mechanisms such as:

- API Gateway throttling
- Usage limits
- WAF
- Application-level quotas
- Authentication-based limits

---

## Timeouts

Every external dependency must have a bounded timeout.

Examples:

```text
Lambda → MongoDB
Lambda → Bedrock
Lambda → External API
Lambda → S3
```

Never allow an external dependency to hang indefinitely.

---

## Idempotency

Operations that can cause duplicate side effects should support idempotency where appropriate.

Example:

```http
Idempotency-Key: abc123
```

Typical candidates:

- Payments
- Orders
- Resource creation
- Job submission
- File processing

Do not blindly retry non-idempotent operations.

---

## Pagination

Do not return unbounded collections.

Prefer:

```text
GET /users?limit=20&cursor=abc
```

instead of returning every record.

For large or changing datasets, cursor-based pagination should be considered.

---

## External Services

Treat every external dependency as potentially unreliable.

Design for:

- Timeout
- Failure
- Retry where safe
- Exponential backoff where appropriate
- Clear failure handling
- Logging
- Fallback where appropriate

Do not blindly retry every operation.

---

## Observability

Production APIs must provide enough information to diagnose failures.

Use:

- Structured logs
- Request/correlation IDs
- Metrics
- Tracing where appropriate
- Alerts

Example:

```text
requestId=req_123
endpoint=/search
userId=user_42
bedrock_started
bedrock_completed
duration=1.82s
```

Never log passwords, tokens, API keys, or unnecessary sensitive information.

---

## Monitoring

Monitor at minimum:

```text
Availability
Latency
Error rate
Throughput
Throttling
Dependency failures
Database failures
External API failures
Cost
```

Important production failures should generate alerts.

---

## Testing

Production APIs should test both successful and failure paths.

Consider:

```text
Unit Tests
Integration Tests
API / Contract Tests
End-to-End Tests
```

Test scenarios such as:

```text
Valid request
Invalid request
Missing fields
Unauthorized request
Forbidden resource
Not found
Duplicate request
Database failure
External API failure
Timeout
Rate limiting
```

---

## Deployment

Prefer:

```text
Git
 ↓
Build
 ↓
Tests
 ↓
Validation
 ↓
Staging
 ↓
Production
```

For AWS/CDK workflows, validate infrastructure changes before deployment.

Production deployment should support safe rollback where practical.

---

## Documentation

Every production endpoint should document:

- Endpoint
- Method
- Authentication
- Authorization
- Parameters
- Request body
- Response
- Error responses
- Examples
- Pagination
- Rate limits where applicable

Prefer OpenAPI/Swagger or another machine-readable API contract when appropriate.

---

## AWS Architecture Guidance

For AWS applications, a common architecture is:

```text
Next.js
   ↓
API Gateway
   ↓
Lambda
   ↓
Validation
   ↓
Authorization
   ↓
Use Case
   ↓
Repository / Service
   ↓
MongoDB / DynamoDB / S3 / Bedrock / External APIs
```

Keep infrastructure concerns separate from application business logic where practical.

---

## Production Readiness Checklist

Before considering an API production-ready:

- [ ] Contract defined
- [ ] Authentication implemented
- [ ] Authorization implemented
- [ ] Input validation implemented
- [ ] Correct HTTP status codes
- [ ] Standardized errors
- [ ] Secrets protected
- [ ] Least-privilege permissions
- [ ] Rate limiting/throttling considered
- [ ] Timeouts configured
- [ ] Idempotency considered
- [ ] Pagination implemented where needed
- [ ] Sensitive fields excluded
- [ ] Structured logging
- [ ] Request IDs
- [ ] Metrics
- [ ] Alerts
- [ ] Failure scenarios tested
- [ ] API documented
- [ ] Backward compatibility considered
- [ ] Deployment/rollback strategy defined