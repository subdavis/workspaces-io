import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from . import database, models, settings


def main():
    con = psycopg2.connect(
        dbname="postgres",
        user=settings.DB_USER,
        port=settings.DB_PORT,
        host=settings.DB_HOST,
        password=settings.DB_PASS,
    )
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE
    cur = con.cursor()

    try:
        cur.execute(
            sql.SQL("DROP DATABASE {}").format(sql.Identifier(settings.DB_NAME))
        )
    except:
        pass
    try:
        cur.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.DB_NAME))
        )
    except:
        pass
    con.close()

    database.Base.metadata.create_all(database.engine)
