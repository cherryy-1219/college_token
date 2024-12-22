from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["MONGO_URI"] = "mongodb://localhost:27017/coderit"

mongo = PyMongo(app)
users = mongo.db.users
tasks = mongo.db.tasks

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.find_one({"email": email})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if users.find_one({"email": email}):
            return 'Email already exists'
        hashed_password = generate_password_hash(password)
        users.insert_one({"email": email, "password": hashed_password})
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/workload_tracker')
def workload_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('workload_tracker.html')

@app.route('/resume_analyzer')
def resume_analyzer():
    return render_template('resume_analyzer.html')

@app.route('/job_suggestions')
def job_suggestions():
    return render_template('job_suggestions.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    task_data = request.json
    task = {
        'name': task_data['name'],
        'dueDate': task_data['dueDate'],
        'completed': False,
        'userId': session['user_id']
    }
    tasks.insert_one(task)
    return jsonify({'status': 'Task added successfully'})

@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    user_tasks = list(tasks.find({'userId': user_id}))
    for task in user_tasks:
        task['_id'] = str(task['_id'])
    return jsonify(user_tasks)

@app.route('/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    tasks.delete_one({'_id': ObjectId(task_id), 'userId': session['user_id']})
    return jsonify({'status': 'Task deleted successfully'})

@app.route('/test_db')
def test_db():
    try:
        mongo.db.command("ping")
        return "Database connected successfully!"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)