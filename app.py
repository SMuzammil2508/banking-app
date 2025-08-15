from flask import Flask, request, render_template, redirect, url_for, session, flash
from functools import wraps
from db import setup_database, get_db
from models import add_transaction, view_passbook
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
setup_database()

# 🔐 Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to continue.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 🔓 Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            session['is_admin'] = bool(user['is_admin'])

            cursor.execute("SELECT name FROM accounts WHERE account_no = ?", (username,))
            account = cursor.fetchone()
            if account:
                session['name'] = account['name']

            flash("Login successful.")
            return redirect(url_for('admin_dashboard') if session['is_admin'] else url_for('home'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

# 🔓 Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# 🏠 Home page
@app.route('/home')
@login_required
def home():
    hour = datetime.now().hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    name = session.get('name', 'User')
    account_no = session.get('username')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE account_no = ?", (account_no,))
    result = cursor.fetchone()
    balance = result['balance'] if result else 0.0

    return render_template('home.html', greeting=greeting, name=name, balance=balance)

# 🧑‍💼 Admin dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    query = request.args.get('query', '').strip().lower()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT account_no, name, balance FROM accounts")
    accounts = cursor.fetchall()

    filtered = [
        acc for acc in accounts
        if not query
        or query in str(acc['account_no'])
        or query in acc['name'].lower()
    ]
    return render_template('admin.html', accounts=filtered, query=query)

# ➕ Add account
@app.route('/admin/add', methods=['POST'])
@login_required
def add_account():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    account_no = request.form['account_no'].strip()
    name = request.form['name'].strip()
    balance = request.form['balance'].strip()

    db = get_db()
    cursor = db.cursor()

    # Check if account already exists
    cursor.execute("SELECT 1 FROM accounts WHERE account_no = ?", (account_no,))
    if cursor.fetchone():
        flash("Account already exists in accounts table.")
        return redirect(url_for('admin_dashboard'))

    # Check if user already exists
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (account_no,))
    if cursor.fetchone():
        flash("Account already exists in users table.")
        return redirect(url_for('admin_dashboard'))

    # Insert into both tables
    cursor.execute("INSERT INTO accounts (account_no, name, balance) VALUES (?, ?, ?)", (account_no, name, balance))
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (account_no, "user123", 0))
    db.commit()

    flash(f"Account {account_no} added successfully.")
    return redirect(url_for('admin_dashboard'))

# 🗑️ Delete account
@app.route('/admin/delete/<account_no>', methods=['POST'])
@login_required
def delete_account(account_no):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM accounts WHERE account_no = ?", (account_no,))
    cursor.execute("DELETE FROM users WHERE username = ?", (account_no,))
    cursor.execute("DELETE FROM transactions WHERE account_no = ?", (account_no,))
    db.commit()
    flash(f"Account {account_no} deleted.")
    return redirect(url_for('admin_dashboard'))

# ✏️ Edit account form
@app.route('/admin/edit/<account_no>', methods=['GET'])
@login_required
def edit_account_form(account_no):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT account_no, name FROM accounts WHERE account_no = ?", (account_no,))
    account = cursor.fetchone()

    if not account:
        flash("Account not found.")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_account.html', account=account)

# ✅ Update account
@app.route('/admin/edit/<account_no>', methods=['POST'])
@login_required
def update_account(account_no):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    new_account_no = request.form['account_no'].strip()
    new_name = request.form['name'].strip()

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE accounts SET account_no = ?, name = ? WHERE account_no = ?", (new_account_no, new_name, account_no))
    cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_account_no, account_no))
    cursor.execute("UPDATE transactions SET account_no = ? WHERE account_no = ?", (new_account_no, account_no))
    db.commit()

    flash("Account updated successfully.")
    return redirect(url_for('admin_dashboard'))

# 💰 Transaction form
@app.route('/transaction_form')
@login_required
def transaction_form():
    return render_template('transaction.html')

# 💸 Submit transaction
@app.route('/transaction', methods=['POST'])
@login_required
def transaction():
    account_no = session.get('username')
    amount = float(request.form['amount'])
    txn_type = request.form['type']
    date_str = request.form.get('date')

    db = get_db()
    cursor = db.cursor()

    # ✅ Check if account exists
    cursor.execute("SELECT 1 FROM accounts WHERE account_no = ?", (account_no,))
    if not cursor.fetchone():
        flash("Transaction failed: account not found.")
        return redirect(url_for('transaction_form'))

    # 🧠 Parse date
    if date_str:
        try:
            txn_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format.")
            return redirect(url_for('transaction_form'))
    else:
        txn_date = datetime.now()

    # 💰 Proceed with transaction
    error = add_transaction(account_no, amount, txn_type, txn_date)
    if error:
        return render_template('transaction_failed.html', message=error), 400

    flash(f"{txn_type.capitalize()} of ₹{amount} successful.")
    return redirect(url_for('home'))

# ONE TIME 
@app.route('/admin/sync_users_to_accounts')
@login_required
def sync_users_to_accounts():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT username FROM users")
    usernames = [row['username'] for row in cursor.fetchall()]

    created = 0
    for username in usernames:
        cursor.execute("SELECT 1 FROM accounts WHERE account_no = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO accounts (account_no, name, balance) VALUES (?, ?, ?)", (username, "Unknown", 0))
            created += 1

    db.commit()
    flash(f"{created} missing accounts created from users.")
    return redirect(url_for('admin_dashboard'))

# 📒 Passbook
@app.route('/passbook')
@login_required
def passbook():
    account_no = request.args.get('account_no', session.get('username'))
    transactions = view_passbook(account_no)

    formatted_txns = []
    for txn in transactions:
        try:
            date_obj = datetime.strptime(txn[3], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            date_obj = datetime.strptime(txn[3], "%Y-%m-%d")
        formatted_txns.append(txn[:3] + (date_obj,))

    return render_template('passbook.html', transactions=formatted_txns, account_no=account_no)

# 🔁 Default route
@app.route('/')
def index():
    return redirect(url_for('login'))

# ❌ 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)