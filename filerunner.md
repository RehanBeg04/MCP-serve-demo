# =========================================================
# Secure MCP Server - Environment Configuration
# Copy to .env and fill in real values. Never commit .env.
# =========================================================

# --- Environment ---
APP_ENV=development                # development | production | testing
APP_NAME=secure-mcp-server
APP_VERSION=1.0.0
LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR
DEBUG=false

# --- Server ---
HOST=0.0.0.0
PORT=8000

# --- Auth mode ---
# "development" -> DevelopmentTokenVerifier (HS256, local secret)
# "azure_ad"    -> AzureADTokenVerifier (JWKS, RS256)
AUTH_MODE=development

# --- Development JWT (only used when AUTH_MODE=development) ---
DEV_JWT_SECRET=change-this-dev-secret-please-32-chars-min
DEV_JWT_ISSUER=https://dev.secure-mcp-server.local
DEV_JWT_AUDIENCE=secure-mcp-server
DEV_JWT_ALGORITHM=HS256

# --- Azure AD (only used when AUTH_MODE=azure_ad) ---
AZURE_TENANT_ID=00000000-0000-0000-0000-000000000000
AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000
AZURE_AUDIENCE=api://00000000-0000-0000-0000-000000000000
AZURE_ISSUER=https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000/v2.0
AZURE_JWKS_URL=https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000/discovery/v2.0/keys
AZURE_JWKS_CACHE_TTL_SECONDS=3600

# --- JWT validation tuning ---
JWT_CLOCK_SKEW_SECONDS=60
JWT_REQUIRED_CLAIMS=sub,iss,aud,exp

# --- OAuth2 Protected Resource Metadata (RFC 9728) ---
RESOURCE_IDENTIFIER=https://mcp.example.com
AUTHORIZATION_SERVERS=https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000/v2.0

# --- CORS ---
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:6274

# --- Security headers ---
ENABLE_HSTS=false                  # set true behind TLS in production

req
# =========================================================
# Secure MCP Server - Production Dependencies
# Python 3.12+
# =========================================================

# --- MCP SDK ---
mcp==1.28.1

# --- Web Framework ---
fastapi==0.115.6
uvicorn[standard]==0.34.0
starlette==0.41.3

# --- Configuration ---
pydantic==2.11.0
pydantic-settings==2.7.1

# --- Authentication / JWT / OAuth2 ---
PyJWT==2.10.1
cryptography==44.0.0
httpx==0.28.1
authlib==1.4.0

# --- Structured Logging ---
structlog==24.4.0

# --- ASGI / Middleware utilities ---
python-multipart==0.0.20
asgiref==3.8.1

# --- Testing ---
pytest==8.3.4
pytest-asyncio==0.25.2
pytest-cov==6.0.0
respx==0.22.0

# --- Dev tooling (optional but included for reproducibility) ---
python-dotenv==1.0.1