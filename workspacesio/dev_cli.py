import posixpath
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Import for creation side-effect
from . import database, models, settings
from .indexing import models as indexing_models


def main():
    database.Base.metadata.create_all(database.engine)
