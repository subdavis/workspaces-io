import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from . import database, models, settings


def main():
    con = psycopg2.connect(settings.SQLALCHEMY_DATABASE_URL + "postgres")
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE
    cur = con.cursor()

    try:
        cur.execute(
            sql.SQL("DROP DATABASE {}").format(
                sql.Identifier(settings.SQLALCHEMY_DBNAME)
            )
        )
    except:
        pass
    try:
        cur.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(settings.SQLALCHEMY_DBNAME)
            )
        )
    except:
        pass

    con.close()

    database.Base.metadata.create_all(database.engine)
