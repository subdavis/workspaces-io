import os

from setuptools import find_packages, setup

deps = [
    "authlib",
    "boto3",
    "click",
    "click-aliases",
    "colorama",
    "cryptography",
    "databases[postgresql]",
    "elasticsearch>=7.0.0,<8.0.0",
    "fastapi",
    "fastapi-users",
    "fastapi-contrib",
    "ffmpeg-python",
    "gunicorn",
    "jinja2",
    "minio",
    "psycopg2-binary",
    "pydantic",
    "pyjwt",
    "requests",
    "requests-toolbelt",
    "sqlalchemy",
    "starlette",
    "tqdm",
    "uvicorn",
]

setup(
    name="workspacesio",
    version="0.1.0",
    script_name="setup.py",
    python_requires=">3.7",
    zip_safe=False,
    install_requires=deps,
    include_package_data=True,
    packages=find_packages(exclude=["test"]),
    entry_points={
        "console_scripts": [
            "wio=workspacesio.cli:cli",
            "workspaces-create-tables=workspacesio.dev_cli:main",
        ],
    },
)
