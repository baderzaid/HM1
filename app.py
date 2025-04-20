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
        # Insert admin if not exists
        conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', ?, 'admin')",
                     (hash_password('admin123'),))

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = hash_password(request.form['password'])

    with sqlite3.connect(DB) as conn:
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            session['user'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid login")
            return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', user=session['user'], role=session['role'])

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


print("Flask is starting...")
