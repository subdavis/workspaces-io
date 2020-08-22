import os
from setuptools import find_packages, setup

# common dependencies
# todo: fully test unified dependencies
# todo: somehow bootstrap building all the sub-dependencies in this project
deps = [
    'boto3',
    'databases[postgresql]',
    'fastapi',
    'fastapi-users',
    'gunicorn',
    'jinja2',
    'psycopg2-binary',
    'pydantic',
    'requests',
    'sqlalchemy',
]

setup(
    name='fastapi-minio-workspaces',
    version='0.1.0',
    script_name='setup.py',
    python_requires='>3.7',
    zip_safe=False,
    install_requires=deps,
    include_package_data=True,
)
