import os

SECRET = os.environ.get('SECRET', 'fast')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'minio')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'minio1234')
AWS_REGION_NAME = 'us-east-1'
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:9000')
DEFAULT_BUCKET = 'fast'
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:example@localhost:5555/fast"
