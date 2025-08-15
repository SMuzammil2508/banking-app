from flask import g
import sqlite3

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("bank.db", check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()
def setup_database():
    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        balance REAL NOT NULL
    )
    """)

    # Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_no TEXT,
        type TEXT,
        amount REAL,
        timestamp TEXT,
        FOREIGN KEY (account_no) REFERENCES accounts(account_no)
    )
    """)

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()