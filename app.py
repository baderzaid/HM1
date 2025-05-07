from flask import Flask, render_template, request, redirect, flash
import sqlite3
import hashlib
from flask import session
import re
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ensure users table exists
def init_db():
    if os.path.exists("users.db"):
        os.remove("users.db")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        national_id TEXT NOT NULL,
        credit_card TEXT NOT NULL,
        valid_date TEXT NOT NULL,
        cvc TEXT NOT NULL
    )
''')
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute('INSERT INTO users (username, password, role, first_name, last_name, national_id, credit_card, valid_date, cvc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
    ('admin', admin_pass, 'admin', 'Israeli', 'Israeili', '123456789', '1234 5567 8901 2345', '12/32', '123'))

    for i in range(1, 10):
        user_pass = hashlib.sha256(f"user{i}pass".encode()).hexdigest()
        c.execute('''
            INSERT INTO users (username, password, role, first_name, last_name, national_id, credit_card, valid_date, cvc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"user{i}", user_pass, 'user',
            f"User{i}", f"Last{i}", f"12345678{i}",
            f"4321 8765 2109 000{i}", "11/30", "111"
        ))
    conn.commit()
    conn.close()

...

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    national_id = request.form['national_id']
    credit_card = request.form['credit_card']
    valid_date = request.form['valid_date']
    cvc = request.form['cvc']

    # Regex validations
    if not re.fullmatch(r'[A-Z][a-z]+', first_name):
        flash("Invalid first name.")
        return redirect('/')
    if not re.fullmatch(r'[A-Z][a-z]+', last_name):
        flash("Invalid last name.")
        return redirect('/')
    if not re.fullmatch(r'\d{9}', national_id):
        flash("Invalid national ID.")
        return redirect('/')
    if not re.fullmatch(r'\d{4} \d{4} \d{4} \d{4}', credit_card):
        flash("Invalid credit card format.")
        return redirect('/')
    if not re.fullmatch(r'(0[1-9]|1[0-2])/\d{2}', valid_date):
        flash("Invalid valid date format.")
        return redirect('/')
    if not re.fullmatch(r'\d{3}', cvc):
        flash("Invalid CVC.")
        return redirect('/')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password, role, first_name, last_name, national_id, credit_card, valid_date, cvc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (username, hashed_password, 'user', first_name, last_name, national_id, credit_card, valid_date, cvc))
        conn.commit()
        conn.close()
        flash('Account created! You can now log in.')
    except sqlite3.IntegrityError:
        flash('Username already exists.')

    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    username_input = request.form['username']
    password_input = request.form['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    is_injection = "' OR 1=1--" in password_input

    if is_injection:
        query = f"SELECT * FROM users WHERE username='{username_input}' AND password='{password_input}'"
    else:
        hashed_password = hashlib.sha256(password_input.encode()).hexdigest()
        query = f"SELECT * FROM users WHERE username='{username_input}' AND password='{hashed_password}'"

    print("Running query:", query)

    try:
        c.execute(query)
        user = c.fetchone()
    except Exception as e:
        conn.close()
        flash(f'SQL Error: {e}')
        return redirect('/')

    conn.close()

    if user:
        session['username'] = user[1]
        session['role'] = user[3]
        return redirect('/admin_panel')
    else:
        flash('Invalid username or password.')
        return redirect('/')


@app.route('/')
def index():
    return render_template('login_signup.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET password=? WHERE username=?', (hashed_password, username))
        if c.rowcount == 0:
            flash('Username not found.')
        else:
            flash('Password has been reset.')
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('reset.html')

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if session.get('role') == 'admin':
        c.execute('SELECT username, role, first_name, last_name, national_id, credit_card, valid_date, cvc FROM users')
        users = c.fetchall()
        result = "<h2>All Users</h2><ul>"
        for u in users:
            result += f"<li>{u}</li>"
        result += "</ul>"
    else:
        c.execute('SELECT username, role, first_name, last_name, national_id, credit_card, valid_date, cvc FROM users WHERE username=?', (session['username'],))
        user = c.fetchone()
        result = "<h2>Your Info</h2><ul>"
        result += f"<li>{user}</li>"
        result += "</ul>"

    conn.close()
    return result

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
