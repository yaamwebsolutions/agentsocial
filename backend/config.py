"""
Application configuration loaded from environment variables.
Automatically loads .env file from project root.
"""

import os
import secrets
from typing import List
from pathlib import Path

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env.local or .env
try:
    from dotenv import load_dotenv

    for env_path in (BASE_DIR / ".env.local", BASE_DIR / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=True)
except ImportError:
    # If python-dotenv is not installed, try to load manually
    for env_file in (BASE_DIR / ".env.local", BASE_DIR / ".env"):
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            break

# =============================================================================
# APPLICATION CONFIG
# =============================================================================
APP_NAME = os.getenv("APP_NAME", "AgentTwitter")
APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# =============================================================================
# SERVER CONFIG
# =============================================================================
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
CORS_ORIGINS: List[str] = (
    os.getenv("CORS_ORIGINS", "*").split(",")
    if os.getenv("CORS_ORIGINS") != "*"
    else ["*"]
)

# =============================================================================
# LOGGING
# =============================================================================
BACKEND_LOG_LEVEL = os.getenv("BACKEND_LOG_LEVEL", "INFO")

# =============================================================================
# DEEPSEEK AI (Primary LLM)
# =============================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_ENABLED = bool(DEEPSEEK_API_KEY)

# =============================================================================
# DATABASE (PostgreSQL)
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_ENABLED = bool(DATABASE_URL)

# =============================================================================
# RESEND EMAIL
# =============================================================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_ENABLED = bool(RESEND_API_KEY)

# =============================================================================
# KlingAI (Video & Image Generation)
# =============================================================================
KLINGAI_ACCESS_KEY = os.getenv("KLINGAI_ACCESS_KEY", "")
KLINGAI_SECRET_KEY = os.getenv("KLINGAI_SECRET_KEY", "")
KLINGAI_API_URL = os.getenv("KLINGAI_API_URL", "https://api-singapore.klingai.com")
KLINGAI_ENABLED = bool(KLINGAI_ACCESS_KEY and KLINGAI_SECRET_KEY)

# =============================================================================
# STOCK VIDEO/IMAGES
# =============================================================================
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_ENABLED = bool(PEXELS_API_KEY and PEXELS_API_KEY != "your-pexels-key")

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
PIXABAY_ENABLED = bool(PIXABAY_API_KEY and PIXABAY_API_KEY != "your-pixabay-key")

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_ENABLED = bool(
    UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your-unsplash-key"
)

# =============================================================================
# MCP (Model Context Protocol)
# =============================================================================
MCP_SERVER_ENABLED = os.getenv("MCP_SERVER_ENABLED", "false").lower() == "true"
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
MCP_SERVER_TRANSPORT = os.getenv("MCP_SERVER_TRANSPORT", "http")
MCP_AUTH_ENABLED = os.getenv("MCP_AUTH_ENABLED", "false").lower() == "true"
MCP_AUTH_PROVIDER = os.getenv("MCP_AUTH_PROVIDER", "google")

# =============================================================================
# SUPABASE
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
SUPABASE_STUDIO_URL = os.getenv("SUPABASE_STUDIO_URL", "")
SUPABASE_GATEWAY_URL = os.getenv("SUPABASE_GATEWAY_URL", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# =============================================================================
# WEB SCRAPING (ScraperAPI)
# =============================================================================
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")
SCRAPERAPI_URL = os.getenv("SCRAPERAPI_URL", "https://api.scraperapi.com")
SCRAPERAPI_ENABLED = bool(SCRAPERAPI_KEY)

# =============================================================================
# SEARCH API (Serper.dev)
# =============================================================================
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_API_URL = os.getenv("SERPER_API_URL", "https://google.serper.dev/search")
SERPER_ENABLED = bool(SERPER_API_KEY)

# =============================================================================
# VIDEO RENDERING (Yaam.ai)
# =============================================================================
YAAM_API_URL = os.getenv("YAAM_API_URL", "https://yaam.ai")
YAAM_RENDER_FROM_URLS = os.getenv("YAAM_RENDER_FROM_URLS", "")
YAAM_RENDER_FROM_PEXELS = os.getenv("YAAM_RENDER_FROM_PEXELS", "")
YAAM_DOWNLOAD = os.getenv("YAAM_DOWNLOAD", "")
YAAM_ENABLED = bool(YAAM_API_URL)


# =============================================================================
# GITHUB OAUTH & API
# =============================================================================
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OAUTH_CALLBACK_URL = os.getenv(
    "GITHUB_OAUTH_CALLBACK_URL", "https://api.yaam.click/auth/github/callback"
)
GITHUB_OAUTH_SCOPE = os.getenv("GITHUB_OAUTH_SCOPE", "read:user user:email repo")
GITHUB_ENABLED = bool(GITHUB_TOKEN or (GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET))

# =============================================================================
# AUTH0 AUTHENTICATION
# =============================================================================
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")  # API identifier
AUTH0_ENABLED = bool(AUTH0_DOMAIN and AUTH0_CLIENT_ID)

# =============================================================================
# AUTHORIZATION
# =============================================================================
# Global auth requirement - when true, all endpoints require authentication
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

# Write operations require authentication (recommended: true for production)
# This protects POST/PUT/DELETE operations even when reads are public
AUTH_REQUIRED_FOR_WRITES = (
    os.getenv("AUTH_REQUIRED_FOR_WRITES", "true").lower() == "true"
)

# =============================================================================
# JWT AUTHENTICATION (fallback/internal)
# =============================================================================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60480")
)  # 7 days

# =============================================================================
# OAUTH STATE (CSRF protection)
# =============================================================================
OAUTH_STATE_SECRET = os.getenv("OAUTH_STATE_SECRET", JWT_SECRET_KEY)
OAUTH_STATE_TTL_SECONDS = int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600"))

# =============================================================================
# REDIS (for caching)
# =============================================================================
REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_ENABLED = bool(REDIS_URL)

# =============================================================================
# AUDIT TRAIL CONFIG
# =============================================================================
# Admin user IDs (comma-separated) who can access audit logs
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "")

# Admin email domains (comma-separated) - users with these domains are admins
ADMIN_EMAIL_DOMAINS = os.getenv("ADMIN_EMAIL_DOMAINS", "")

# Audit log retention in days (0 = keep forever)
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))

# Enable detailed audit logging (logs all API requests)
AUDIT_DETAILED_LOGGING = os.getenv("AUDIT_DETAILED_LOGGING", "true").lower() == "true"

# =============================================================================
# AGENT CONFIG
# =============================================================================
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "30"))
MAX_THREAD_LENGTH = int(os.getenv("MAX_THREAD_LENGTH", "100"))
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "true").lower() == "true" or DEEPSEEK_ENABLED
AGENTS_CONFIG_PATH = os.getenv(
    "AGENTS_CONFIG_PATH", str(BASE_DIR / "backend" / "agents.json")
)
AGENTS_CONFIG_STRICT = os.getenv("AGENTS_CONFIG_STRICT", "false").lower() == "true"
if AGENTS_CONFIG_PATH and not Path(AGENTS_CONFIG_PATH).is_absolute():
    AGENTS_CONFIG_PATH = str((BASE_DIR / AGENTS_CONFIG_PATH).resolve())


def print_config():
    """Print current configuration (for debugging)"""
    print(f"=== {APP_NAME} Configuration ===")
    print(f"Environment: {APP_ENV}")
    print(f"Version: {APP_VERSION}")
    print(f"Server: {BACKEND_HOST}:{BACKEND_PORT}")
    print(f"CORS Origins: {CORS_ORIGINS}")
    print(f"Log Level: {BACKEND_LOG_LEVEL}")
    print(f"Agents Config: {AGENTS_CONFIG_PATH}")
    print(f"Auth Required: {AUTH_REQUIRED}")
    print("\n--- Services Status ---")
    print(f"DeepSeek LLM: {'ENABLED' if DEEPSEEK_ENABLED else 'DISABLED (using mock)'}")
    print(
        f"PostgreSQL DB: {'ENABLED' if DATABASE_ENABLED else 'DISABLED (using in-memory)'}"
    )
    print(f"Serper Search: {'ENABLED' if SERPER_ENABLED else 'DISABLED'}")
    print(f"ScraperAPI: {'ENABLED' if SCRAPERAPI_ENABLED else 'DISABLED'}")
    print(f"KlingAI: {'ENABLED' if KLINGAI_ENABLED else 'DISABLED'}")
    print(f"Pexels: {'ENABLED' if PEXELS_ENABLED else 'DISABLED'}")
    print(f"Resend Email: {'ENABLED' if RESEND_ENABLED else 'DISABLED'}")
    print(f"Supabase: {'ENABLED' if SUPABASE_ENABLED else 'DISABLED'}")
    print(f"Yaam.ai: {'ENABLED' if YAAM_ENABLED else 'DISABLED'}")
    print(f"GitHub API: {'ENABLED' if GITHUB_ENABLED else 'DISABLED'}")
    print(f"Auth0: {'ENABLED' if AUTH0_ENABLED else 'DISABLED'}")
    print(f"Redis: {'ENABLED' if REDIS_ENABLED else 'DISABLED'}")
    print(
        f"Audit Trail: {'ENABLED (detailed logging)' if AUDIT_DETAILED_LOGGING else 'ENABLED (basic)'}"
    )
    print(
        f"Admin Users: {len([x for x in ADMIN_USER_IDS.split(',') if x]) if ADMIN_USER_IDS else 0} configured"
    )
    print("=" * 40)


if __name__ == "__main__":
    print_config()
