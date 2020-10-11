import os
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    public_name: str = "http://localhost:8100"
    database_uri: str = f"postgresql:///wio"
    secret: str = "secret"

    es_nodes: List[str] = ["http://localhost:9200"]

    oidc_name: str = "auth0"
    oidc_client_id: str
    oidc_client_secret: str
    oidc_well_known_url: str
    oidc_algos: List[str] = ["RS256"]

    class Config:
        env_prefix = "wio_"
        env_file = os.getenv("DOTENV_PATH", ".env")


settings = Settings()
