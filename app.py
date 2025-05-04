from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'
DB = 'users.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with sqlite3.connect(DB) as conn:
        with open('schema.sql') as f:
            conn.executescript(f.read())

        users = [
            ("admin", "admin123", "admin"),
            ("bader", "bader123", "user"),
            ("zaid", "zaid123", "user"),
            ("yazan", "yazan123", "user"),
            ("sara", "sara123", "user"),
            ("nada", "nada123", "user"),
            ("ahmad", "ahmad123", "admin"),
            ("mhmd", "mhmd123", "user"),
            ("wasem", "wasem123", "user"),
            ("emad", "emad123", "user"),
        ]

        for i, (u, p, r) in enumerate(users, start=1):
            conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (?, ?, ?, ?)",
                         (i, u, hash_password(p), r))

        cards = [
            ("Israeli", "Israeili", "123456789", "1234 5567 8901 2345", "12/32", "123"),
            ("bader", "zaid", "987654321", "1111 2222 3333 4444", "11/30", "456"),
            ("zaid", "zaid", "456789123", "5555 6666 7777 8888", "10/28", "789"),
            ("yazan", "zaid", "321654987", "9999 0000 1111 2222", "09/26", "321"),
            ("sara", "zaid", "741852963", "3333 4444 5555 6666", "08/27", "147"),
            ("nada", "zaid", "852963741", "7777 8888 9999 0000", "07/29", "258"),
            ("ahmad", "zaid", "159357258", "2468 1357 8642 7531", "06/31", "369"),
            ("mhmd", "kabha", "357951456", "1357 2468 3579 4680", "05/25", "951"),
            ("waseem", "abo helal", "258456123", "4321 8765 2109 6543", "04/24", "753"),
            ("emad", "khateeb", "951753852", "6543 2109 8765 4321", "03/23", "159"),
        ]

        for i, card in enumerate(cards, start=1):
            conn.execute("""
                INSERT OR IGNORE INTO credit_cards
                (user_id, first_name, last_name, id_number, card_number, valid_date, cvc)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (i, *card))

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = hash_password(request.form['password'])

    with sqlite3.connect(DB) as conn:
        # ⚠️ Vulnerable query for SQL Injection
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        user = conn.execute(query).fetchone()

        if user:
            session['user'] = user[1]
            session['role'] = user[3]
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid login")
            return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))

    cards = []
    if session['role'] == 'admin':
        with sqlite3.connect(DB) as conn:
            cards = conn.execute("""
                SELECT u.username, c.first_name, c.last_name, c.id_number,
                       c.card_number, c.valid_date, c.cvc
                FROM credit_cards c JOIN users u ON u.id = c.user_id
            """).fetchall()
    return render_template('dashboard.html', user=session['user'], role=session['role'], cards=cards)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/reset')
def reset():
    return render_template('reset_password.html')

@app.route('/new-password', methods=['POST'])
def new_password():
    username = request.form['username']
    new_pass = hash_password(request.form['new_password'])

    with sqlite3.connect(DB) as conn:
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user:
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_pass, username))
            flash("Password updated")
        else:
            flash("User not found")
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists(DB):
        init_db()
    app.run(debug=True)
