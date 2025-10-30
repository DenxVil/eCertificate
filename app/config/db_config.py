"""Database configuration for SQLite."""
import os

def get_database_uri() -> str:
    """Read DATABASE_URL from environment or use SQLite default."""
    uri = os.getenv("DATABASE_URL")
    if not uri:
        # Default to SQLite in the application directory
        uri = "sqlite:///ecertificate.db"
    return uri
