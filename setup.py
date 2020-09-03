import os

from setuptools import setup

deps = [
    "boto3",
    "click",
    "click-aliases",
    "colorama",
    "databases[postgresql]",
    "elasticsearch>=7.0.0,<8.0.0",
    "fastapi",
    "fastapi-users",
    "gunicorn",
    "jinja2",
    "minio",
    "psycopg2-binary",
    "pydantic",
    "requests",
    "requests-toolbelt",
    "sqlalchemy",
    "tqdm",
]

setup(
    name="workspacesio",
    version="0.1.0",
    script_name="setup.py",
    python_requires=">3.7",
    zip_safe=False,
    install_requires=deps,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "wio=workspacesio.cli:cli",
            "workspaces-create-tables=workspacesio.dev_cli:main",
        ],
    },
)
