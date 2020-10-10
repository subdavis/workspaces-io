import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

SECRET = os.environ.get("WIO_SECRET", "fast")
PUBLIC_NAME = os.environ.get("WIO_PUBLIC_NAME", "http://localhost:8100").rstrip("/")
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "WIO_DATABASE_URL",
    f"postgresql://wio:workspaces@localhost:5555/wio",
)
ES_NODE_1 = os.environ.get("WIO_ELASTICSEARCH_NODE_1", "http://localhost:9200")
ES_NODES = [ES_NODE_1]

KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "master")
# URL for clients to access keycloak
KEYCLOAK_PUBLIC_URL = os.environ.get("KEYCLOAK_PUBLIC_URL", "http://localhost:8200")
# URL for workspaces to access keycloak directly
KEYCLOAK_PRIVATE_URL = os.environ.get("KEYCLOAK_PRIVATE_URL", KEYCLOAK_PUBLIC_URL)
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "wio")

KEYCLOAK_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    f"{os.environ.get('KEYCLOAK_PUBLIC_KEY', '')}\n"
    "-----END PUBLIC KEY-----\n"
)
