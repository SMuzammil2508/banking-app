import sqlite3
from flask import g

DATABASE = "bank.db"

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, timeout=5, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def setup_database():
    with sqlite3.connect(DATABASE, timeout=5, check_same_thread=False) as conn:
        cursor = conn.cursor()

        # Enable WAL mode for concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")

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

        # Create beneficiaries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS beneficiaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            account_no TEXT NOT NULL,
            FOREIGN KEY (account_no) REFERENCES accounts(account_no),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        conn.commit()