from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

import os

app = Flask(__name__)

app.secret_key = os.urandom(24)

users = {}

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            msg = "Username already exists"
        elif not username.isalnum():
            msg = "Username is not valid"
        else:
            hashed = generate_password_hash(password)
            users[username] = hashed
            return redirect('/login')
    return render_template('register.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect('/member')
        else:
            msg = "Invalid username or password"
    return render_template('login.html', msg=msg)

@app.route('/member')
def member():
    if 'username' not in session:
        return redirect('/login')
    return f"Welcome {session['username']}! <a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
