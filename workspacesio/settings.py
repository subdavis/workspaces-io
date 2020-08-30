import os

SECRET = os.environ.get("SECRET", "fast")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "backend")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "backend1234")
AWS_REGION_NAME = "us-east-1"
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:9000")
DEFAULT_BUCKET = "fast"

DB_NAME = "fast"
DB_USER = "postgres"
DB_PASS = "example"
DB_HOST = "localhost"
DB_PORT = "5555"
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

ES_NODES = [{"host": "localhost"}]
