from flask import g
import psycopg2
from psycopg2.extras import DictCursor 
#from dotenv import load_dotenv # to run env variables locally
import os

#load_dotenv() # to run env variables locally
database_url = os.getenv('DATABASE_URL')

def connect_db():
    # Added URI from Heroku
    conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
    conn.autocommit = True # This is optional. In Postgres the connection object and cursor object are separate, the commit is on the connection, and the queries are run on the cursor
    sql = conn.cursor() # Creates a cursor to run the commands

    return conn, sql


def get_db():
    db = connect_db()

    if not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn = db[0]
    
    if not hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur


def init_db():
    db = connect_db()

    # Create tables as per schema.sql
    db[1].execute(open('schema.sql', 'r').read())

    # Close the connection and the cursor
    db[1].close()
    db[0].close()


def init_admin():
    db = connect_db()

    db[1].execute('UPDATE users SET admin = True WHERE name = %s', ('admin', ))

    db[1].close()
    db[0].close


