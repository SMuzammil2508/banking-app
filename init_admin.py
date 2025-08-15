# init_admin.py

from app import app
from db import get_db

with app.app_context():
    db = get_db()
    cursor = db.cursor()

    # ✅ Ensure 'date' and 'description' columns exist in transactions table
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'date' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN date TEXT")
        print("✅ 'date' column added to transactions table.")
    else:
        print("ℹ️ 'date' column already exists.")

    if 'description' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN description TEXT")
        print("✅ 'description' column added to transactions table.")
    else:
        print("ℹ️ 'description' column already exists.")

    # ✅ Create admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("8097832781",))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute("""
            INSERT INTO users (username, password, is_admin)
            VALUES (?, ?, ?)
        """, ("8097832781", "ADMIN123", 1))
        print("✅ Admin user created.")
    else:
        print("⚠️ Admin user already exists.")

    # ✅ Create admin account if not exists
    cursor.execute("SELECT * FROM accounts WHERE account_no = ?", ("8097832781",))
    account_exists = cursor.fetchone()

    if not account_exists:
        cursor.execute("""
            INSERT INTO accounts (account_no, name, balance)
            VALUES (?, ?, ?)
        """, ("8097832781", "Admin", 0))
        print("✅ Admin account created.")
    else:
        print("⚠️ Admin account already exists.")

    db.commit()