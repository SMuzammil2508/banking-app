from db import get_db
from app import app  # Import your Flask app

def show_users():
    with app.app_context():  # 🔧 This sets up the Flask context
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username, password, is_admin FROM users")
        users = cursor.fetchall()

        print("📋 Users in database:")
        for user in users:
            print(f"Username: {user['username']}, Password: {user['password']}, Admin: {bool(user['is_admin'])}")

if __name__ == "__main__":
    show_users()