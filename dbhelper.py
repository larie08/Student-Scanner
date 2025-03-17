# dbhelper.py
import sqlite3

def connect_db():
    return sqlite3.connect("personlist.db")

def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS USERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idno TEXT UNIQUE,
            lastname TEXT,
            firstname TEXT,
            course TEXT,
            level TEXT,
            photo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USERS WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def getall_process(sql: str, params=())-> bool:
    db = connect(database)
    db.row_factory = Row
    cursor = db.cursor()
    cursor.execute(sql, params)
    data = cursor.fetchall()
    db.close()
    return data
    
def getall_records(table: str) -> list:
    sql = f"SELECT * FROM `{table}`"
    return getall_process(sql)