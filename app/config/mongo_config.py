import os

def get_mongo_uri() -> str:
    """Read MONGO_URI from environment and raise a helpful error if missing."""
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError(
            "MONGO_URI environment variable is not set.\n"
            "For local development with docker-compose, use: mongodb://mongo:27017/eCertificate\n"
            "If MongoDB runs on the host (Docker Desktop), use: mongodb://host.docker.internal:27017/eCertificate\n"
            "Or use a MongoDB Atlas connection string."
        )
    return uri
