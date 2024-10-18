from flask import g
import psycopg2
from psycopg2.extras import DictCursor 

def connect_db():
    # Added URI from Heroku
    conn = psycopg2.connect('postgres://uelmv0cs53ceh8:p14088bb491a08e41ebe57c7da4ec0ed9e1fbafe8fb7b6e1f0050063807ee4441@ccaml3dimis7eh.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/d9r6pgeht3ff6q', cursor_factory=DictCursor)
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

# Source to fix libpq errors on macOS - https://github.com/orgs/Homebrew/discussions/3595
# How to fix psycopg2 errors:
# activate virtual environment: $ source .venv/bin/activate
# check Python version: $ python --version
# $ pip install psycopg2
# $ pip install psycopg2-binary <-- the magic that fixed the error
# $ pip show psycopg2
# run the app: $ python app.py


