from db import get_db
from datetime import datetime

# ➕ Add transaction with optional date
def add_transaction(account_no, amount, txn_type, txn_date=None):
    db = get_db()
    cursor = db.cursor()

    # Fetch current balance
    cursor.execute("SELECT balance FROM accounts WHERE account_no = ?", (account_no,))
    result = cursor.fetchone()
    if not result:
        return "Account not found."

    current_balance = result['balance']

    # Calculate new balance
    if txn_type == "deposit":
        new_balance = current_balance + amount
    elif txn_type == "withdraw":
        if amount > current_balance:
            return "Insufficient balance."
        new_balance = current_balance - amount
    else:
        return "Invalid transaction type."

    # Use provided date or fallback to now
    if txn_date is None:
        txn_date = datetime.now()
    elif isinstance(txn_date, str):
        try:
            txn_date = datetime.strptime(txn_date, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format."

    # Update balance and insert transaction
    cursor.execute("UPDATE accounts SET balance = ? WHERE account_no = ?", (new_balance, account_no))
    cursor.execute("""
        INSERT INTO transactions (account_no, amount, type, date)
        VALUES (?, ?, ?, ?)
    """, (account_no, amount, txn_type, txn_date.strftime("%Y-%m-%d %H:%M:%S")))

    db.commit()
    return None

def add_transaction(account_no, amount, txn_type, date):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO transactions (account_no, amount, type, date)
        VALUES (?, ?, ?, ?)
    """, (account_no, amount, txn_type, date))
    db.commit()

# 📒 View passbook
def view_passbook(account_no):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT account_no, amount, type, date
        FROM transactions
        WHERE account_no = ?
        ORDER BY date DESC
    """, (account_no,))
    return cursor.fetchall()