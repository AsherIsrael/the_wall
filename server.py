from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
app = Flask(__name__)
app.secret_key = "thiskeyhere"
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app, "the_wall")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=["POST"])
def login():
    email = request.form['email']
    password = request.form['password']

    error = ''

    query = "SELECT * FROM users WHERE email = :email"
    try_user = mysql.query_db(query, {'email':email})

    if try_user:
        if bcrypt.check_password_hash(try_user[0]['pass_encrypt'], password):
            session['user_id'] = try_user[0]['id']
            return redirect('/wall')
        else:
            flash("invalid username or password")
            return redirect('/')
    else:
        flash("invalid username or password")
        return redirect('/')


@app.route('/registration', methods=["POST"])
def registration():
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    password = request.form['password']
    pass_confirm = request.form['pass_confirm']

    errors = []

    if len(fname) < 2:
        errors.append('First name must be at least 2 characters')
    if len(lname) < 2:
        errors.append('Last name must be at least 2 characters')
    if not fname.isalpha() or not lname.isalpha():
        errors.append('Names can only contain letters')
    if not EMAIL_REGEX.match(email):
        errors.append('Must enter a valid email')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters')
    elif not password == pass_confirm:
        errors.append('Password and confirmaton must match')

    if errors:
        for error in errors:
            flash(error)

        return redirect('/')
    else:
        pass_encrypt = bcrypt.generate_password_hash(password)
        query = "INSERT INTO users (fname, lname, email, pass_encrypt, created_at) VALUES (:fname, :lname, :email, :pass_encrypt, NOW())"
        data = {'fname':fname, 'lname':lname, 'email':email, 'pass_encrypt':pass_encrypt}
        session['user_id'] = mysql.query_db(query, data)
        return redirect('/wall')

@app.route('/wall')
def wall():
    message_query = "SELECT CONCAT(users.fname, ' ', users.lname) as name, messages.message, messages.id, messages.created_at FROM messages JOIN users ON users.id = messages.user_id ORDER BY messages.created_at DESC"
    messages = mysql.query_db(message_query)
    comment_query = "SELECT CONCAT(users.fname, ' ', users.lname) as name, comments.comment, comments.message_id, comments.created_at FROM comments JOIN users ON users.id = comments.user_id"
    comments = mysql.query_db(comment_query)
    user_query = "SELECT * FROM users WHERE id = :id"
    user = mysql.query_db(user_query, {'id':session['user_id']})[0]
    return render_template('wall.html', user=user, messages=messages, comments=comments)

@app.route('/messages', methods=['POST'])
def create_message():
    message = request.form['message']
    query = "INSERT INTO messages (user_id, message, created_at) VALUES (:user_id, :message, NOW())"
    data = {'user_id':session['user_id'], 'message':message}
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/comments', methods=['POST'])
def create_comment():
    comment = request.form['comment']
    message_id = request.form['message_id']
    query = "INSERT INTO comments (user_id, message_id, comment, created_at) VALUES (:user_id, :message_id, :comment, NOW())"
    data = {'user_id':session['user_id'], 'message_id':message_id, 'comment':comment}
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)
