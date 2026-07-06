# Secure MCP Server - Full Flow and Component Overview

This document explains the end-to-end flow of the MCP service, the main components involved, and the core artifacts and dependencies used by the system.

## 1. What this server is doing

The application exposes:

- a standard FastAPI HTTP surface for health checks and OAuth metadata
- an MCP Streamable HTTP endpoint mounted at `/mcp`
- authenticated MCP tool execution with RBAC and audit logging

The architecture is designed so that every MCP tool call passes through authentication, authorization, auditing, and structured logging before execution.

---

## 2. High-level architecture

```mermaid
flowchart TD
    Client[Client / MCP Consumer] -->|HTTP + Bearer token| FastAPI[FastAPI App]
    FastAPI --> Middleware[Security Middleware]
    Middleware --> MCPMount[/mcp mount]
    MCPMount --> AuthMW[MCPAuthenticationMiddleware]
    AuthMW --> TokenVerifier[TokenVerifier]
    TokenVerifier --> Principal[UserPrincipal]
    Principal --> Context[ContextVars]
    Context --> Session[dispatch_tool_call]
    Session --> RBAC[RBAC check]
    RBAC --> Audit[Audit logging]
    Audit --> Tool[Tool handler]
    Tool --> Response[JSON/text response]
```

---

## 3. Main artifacts and modules

### Runtime entrypoint
- [app/main.py](app/main.py)
- Creates the FastAPI app
- Registers middleware
- Registers REST routes for health and OAuth metadata
- Mounts the MCP application under `/mcp`

### MCP transport layer
- [app/mcp/server.py](app/mcp/server.py)
- Builds the MCP server
- Registers tool definitions
- Routes tool calls into the centralized dispatch layer

### MCP authentication boundary
- [app/mcp/authentication.py](app/mcp/authentication.py)
- Runs before the MCP session is established
- Extracts the Bearer token from the request
- Verifies it using the configured token verifier
- Binds the authenticated principal to request context

### MCP session dispatch
- [app/mcp/session.py](app/mcp/session.py)
- Central entrypoint for tool execution
- Runs RBAC checks and audit-wrapped execution

### Tool implementations
- [app/mcp/tools.py](app/mcp/tools.py)
- Implements the actual MCP tools:
  - `hello`
  - `who_am_i`
  - `get_weather`
  - `delete_record`

### Authentication and identity
- [app/auth/jwt_validator.py](app/auth/jwt_validator.py)
- [app/auth/principal.py](app/auth/principal.py)
- [app/auth/context.py](app/auth/context.py)
- [app/auth/rbac.py](app/auth/rbac.py)
- [app/auth/exceptions.py](app/auth/exceptions.py)

These modules handle:
- token verification
- conversion of claims into a user identity
- role-based access control
- request-scoped propagation of principal data

### Configuration
- [app/config.py](app/config.py)
- Central configuration source using Pydantic settings
- Supports:
  - development JWT mode
  - Azure AD / OIDC mode
  - environment-specific behavior
  - CORS and security settings

### Logging and auditing
- [app/logging/logger.py](app/logging/logger.py)
- [app/logging/audit.py](app/logging/audit.py)
- Structured logging with correlation IDs
- Separate audit events for auth, authorization, and tool execution

### API endpoints
- [app/api/health.py](app/api/health.py)
- [app/api/oauth_metadata.py](app/api/oauth_metadata.py)
- Health endpoint
- OAuth protected resource metadata endpoint for RFC 9728 discovery

### Schemas and contracts
- [app/models/schemas.py](app/models/schemas.py)
- Defines request/response models for the tools and API errors

---

## 4. Full request flow

### A. Startup
1. The app loads settings from [app/config.py](app/config.py).
2. Logging is configured through [app/logging/logger.py](app/logging/logger.py).
3. The FastAPI app is created in [app/main.py](app/main.py).
4. Middleware is registered.
5. REST routes and the MCP mount are attached.
6. A token verifier is created based on the selected auth mode.

### B. Incoming request to `/mcp`
1. The client sends an HTTP request to the MCP endpoint.
2. The request passes through the standard FastAPI middleware stack.
3. The request is intercepted by [app/mcp/authentication.py](app/mcp/authentication.py).
4. The middleware extracts the Bearer token.
5. The token is verified.
6. If valid, a `UserPrincipal` is created and bound to request context.
7. If invalid, the request is rejected with a JSON error response.

### C. MCP tool call
1. The MCP transport layer in [app/mcp/server.py](app/mcp/server.py) receives the tool request.
2. It resolves the requested tool name and forwards the call to [app/mcp/session.py](app/mcp/session.py).
3. The dispatch layer performs RBAC checks.
4. An audit span is started for execution.
5. The tool implementation in [app/mcp/tools.py](app/mcp/tools.py) runs.
6. The result is serialized and returned to the client.

### D. Security checks in order
The request is protected by multiple layers:

1. Transport-level authentication
2. Request-scoped principal binding
3. Role-based authorization
4. Tool-level decorator enforcement
5. Structured audit logging

This makes the system defense-in-depth rather than relying on a single gate.

---

## 5. Supported MCP tools

| Tool | Purpose | Required role |
|---|---|---|
| `hello` | Returns a greeting for the authenticated user | Any authenticated user |
| `who_am_i` | Returns user identity, roles, tenant, and claims | Any authenticated user |
| `get_weather` | Returns sample weather for a city | Reader or above |
| `delete_record` | Deletes a record by ID | Admin |

---

## 6. Authentication modes

### Development mode
- Uses signed development JWTs with HS256
- Intended for local development
- Configured via settings such as `dev_jwt_secret`

### Azure AD mode
- Uses Azure AD-issued JWTs validated with JWKS
- Suitable for production or enterprise deployments
- Requires tenant, audience, issuer, and JWKS configuration

---

## 7. Dependencies in use

The project uses the following main libraries from [requirements.txt](requirements.txt):

- `mcp` for the MCP protocol and server implementation
- `fastapi` and `starlette` for the HTTP layer
- `uvicorn` for serving the application
- `pydantic` and `pydantic-settings` for models and configuration
- `PyJWT` and `cryptography` for JWT validation
- `httpx` for HTTP-based JWKS access
- `structlog` for structured logging
- `pytest` and `pytest-asyncio` for testing

---

## 8. Design principles in this codebase

- Authentication happens before MCP session establishment
- Principal identity is request-scoped and propagated safely
- RBAC is enforced in both the session layer and tool layer
- Audit logs are emitted for security-relevant events
- Errors are handled centrally and consistently
- Configuration is environment-driven rather than hardcoded

---

## 9. Summary

The server is a secure MCP endpoint built on FastAPI and the MCP SDK. A request is accepted only after successful authentication, then routed through RBAC and audit layers before the target tool is executed. The design emphasizes security, traceability, and clean separation between transport, authentication, authorization, and tool implementation.
