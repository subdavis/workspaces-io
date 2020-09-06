import posixpath
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Import for creation side-effect
from . import database, models, settings
from .indexing import models as indexing_models


def main():
    # if len(sys.argv) > 1:
    #     con = psycopg2.connect(
    #         posixpath.join(settings.SQLALCHEMY_DATABASE_URL, settings.SQLALCHEMY_DBNAME)
    #     )
    #     con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE
    #     cur = con.cursor()

    #     try:
    #         cur.execute(
    #             sql.SQL("DROP DATABASE {}").format(
    #                 sql.Identifier(settings.SQLALCHEMY_DBNAME)
    #             )
    #         )
    #     except:
    #         pass
    #     try:
    #         cur.execute(
    #             sql.SQL("CREATE DATABASE {}").format(
    #                 sql.Identifier(settings.SQLALCHEMY_DBNAME)
    #             )
    #         )
    #     except:
    #         pass

    #     con.close()

    database.Base.metadata.create_all(database.engine)
