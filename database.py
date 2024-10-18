from flask import g
import sqlite3

def connect_db():
    sql = sqlite3.connect('/Users/nataliepeyre/Documents/CD/UDEMY_FLASK_COURSE/qna_app/questions.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db