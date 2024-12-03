from flask import Flask, request, render_template, redirect, url_for, flash

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
app.secret_key = '0a96bcc1a990df163e539b3c39bca6ce'

# Load data from JSON files
def load_data(filename, user_id=None):
    try:
        if user_id:
            filepath = f'data/message/{user_id}.json'
        else:
            filepath = f'data/{filename}'
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}

# Save data to JSON files
def save_data(filename, data, user_id=None):
    try:
        if user_id:
            filepath = f'data/message/{user_id}.json'
        else:
            filepath = f'data/{filename}'
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving data: {e}")

# Save CV to user-specific directory
def save_cv(user_id, cv_file):
    if cv_file and cv_file.filename:
        filename = secure_filename(cv_file.filename)
        directory = os.path.join('uploads', str(user_id), 'cv')
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = os.path.join(directory, filename)
        cv_file.save(file_path)
        return filename
    return None

# Load user details
def load_user(email):
    users = load_data('users.json')
    return next((u for u in users['users'] if u['username'] == email), None)

# Update user details
def update_user(email, full_name, phone):
    users = load_data('users.json')
    user = next((u for u in users['users'] if u['username'] == email), None)
    if user:
        user['full_name'] = full_name
        user['phone'] = phone
        save_data('users.json', users)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return render_template('register.html', error="All fields are required.")

        users = load_data('users.json')

        # Check if username or email already exists
        if any(u['username'] == username or u['username'] == email for u in users.get('users', [])):
            return render_template('register.html', error="Username or email already exists.")

        # Determine role based on email domain
        if email.endswith('@admin.com'):
            role = 'admin'
        else:
            role = 'candidate'

        # Add new user
        new_user = {'username': username, 'email': email, 'password': password, 'role': role}
        users.setdefault('users', []).append(new_user)

        save_data('users.json', users)

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template('login.html', error="Email and password are required.")

        users = load_data('users.json')

        # Check if the user exists and the password matches
        user = next((u for u in users['users'] if u['email'] == email and u['password'] == password), None)
        if user:
            session['username'] = user['username']  # Use username for session
            session['user_id'] = user.get('id', email)  # Assuming 'id' is part of user data
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            else:
                return redirect(url_for('dashboard'))  # Redirect to candidate dashboard
        else:
            return render_template('login.html', error="Invalid email or password.")

    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    email = session['username']
    
    # Load applied jobs and results
    jobs = load_data('jobs.json')
    results = load_data('results.json')

    applied_jobs = [job for job in jobs['jobs'] if any(res['username'] == email and res['job_id'] == job['id'] for res in results['results'])]
    user_results = [res for res in results['results'] if res['username'] == email]

    return render_template('dashboard.html', username=email, applied_jobs=applied_jobs, user_results=user_results)

@app.route('/jobs')
def jobs():
    if 'username' not in session:
        return redirect(url_for('login'))

    jobs_data = load_data('jobs.json')
    return render_template('jobs.html', jobs=jobs_data['jobs'])

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    job_data = load_data('jobs.json')
    job = next((job for job in job_data['jobs'] if job['id'] == job_id), None)

    if request.method == 'POST':
        if 'cv' in request.files:
            # Handle CV upload
            cv_file = request.files.get('cv')
            filename = save_cv(session['user_id'], cv_file)

            # Save the CV details
            results = load_data('results.json')
            new_result = {
                'username': session['username'],
                'job_id': job_id,
                'cv_filename': filename,
                'answers': {},
                'status': 'Assessment Pending'
            }
            results['results'].append(new_result)
            save_data('results.json', results)

            # Load assessment questions
            test_data = load_data('test_data.json')
            job_type = job['title']
            questions = test_data.get(job_type, [])

            return render_template('assessment.html', job=job, questions=questions)

    return render_template('job_detail.html', job=job)

@app.route('/submit_assessment/<int:job_id>', methods=['POST'])
def submit_assessment(job_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    job_data = load_data('jobs.json')
    job = next((job for job in job_data['jobs'] if job['id'] == job_id), None)

    # Load assessment questions
    test_data = load_data('test_data.json')
    job_type = job['title']
    questions = test_data.get(job_type, [])

    # Process submitted answers
    submitted_answers = {f'question{i+1}': request.form.get(f'question{i+1}') for i in range(len(questions))}

    results = load_data('results.json')
    result = next((res for res in results['results'] if res['username'] == session['username'] and res['job_id'] == job_id), None)
    
    if result:
        # Update existing result
        result['answers'] = submitted_answers
        result['status'] = 'Submitted'
    else:
        # Add new result
        new_result = {
            'username': session['username'],
            'job_id': job_id,
            'answers': submitted_answers,
            'status': 'Submitted'
        }
        results['results'].append(new_result)

    save_data('results.json', results)

    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    email = session['username']
    user = load_user(email)

    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        update_user(email, full_name, phone)
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/help', methods=['GET', 'POST'])
def help():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['username']
    if request.method == 'POST':
        message = request.form['message']
        messages = load_data('messages.json', user_id=user_id)

        # Ensure 'messages' key exists
        if 'messages' not in messages:
            messages['messages'] = []

        new_message = {'username': session['username'], 'message': message}
        messages['messages'].append(new_message)
        save_data('messages.json', messages, user_id=user_id)
        return redirect(url_for('help'))

    messages = load_data('messages.json', user_id=user_id)
    # Ensure 'messages' key exists
    if 'messages' not in messages:
        messages['messages'] = []

    return render_template('help.html', messages=messages['messages'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or not any(u['username'] == session['username'] and u['role'] == 'admin' for u in load_data('users.json')['users']):
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html')

@app.route('/admin/jobs')
def admin_jobs():
    if 'username' not in session or not any(u['username'] == session['username'] and u['role'] == 'admin' for u in load_data('users.json')['users']):
        return redirect(url_for('login'))
    
    jobs = load_data('jobs.json')
    return render_template('admin_jobs.html', jobs=jobs['jobs'])

@app.route('/create_quiz', methods=['POST'])
def create_quiz():
    job_id = request.form.get('job_id')
    question = request.form.get('question')
    options = request.form.get('options').split(',')

    with open('test_data.json', 'r+') as file:
        data = json.load(file)
        if job_id not in data:
            data[job_id] = []
        data[job_id].append({
            'question_id': len(data[job_id]) + 1,
            'question': question,
            'options': options
        })
        file.seek(0)
        json.dump(data, file, indent=4)

    return redirect(url_for('admin_jobs'))

@app.route('/create_job', methods=['POST'])
def create_job():
    job_title = request.form['job_title']
    job_description = request.form['job_description']
    
    # Load existing jobs from file
    jobs = load_data('jobs.json')
    
    # Generate a new ID (incremental or based on the highest ID)
    if jobs.get('jobs'):
        # Ensure all jobs have an 'id'
        for job in jobs['jobs']:
            if 'id' not in job:
                job['id'] = None  # Assign a default value to identify entries without an ID

        # Generate a new ID based on the highest existing ID
        new_id = max((job['id'] for job in jobs['jobs'] if job['id'] is not None), default=0) + 1
    else:
        new_id = 1
    
    # Create a new job entry
    new_job = {
        'id': new_id,
        'title': job_title,
        'description': job_description
    }
    
    # Add new job to the list and save
    jobs.setdefault('jobs', []).append(new_job)
    save_data('jobs.json', jobs)
    
    return redirect(url_for('admin_jobs'))

@app.route('/admin/messages', methods=['GET', 'POST'])
def admin_messages():
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        message = request.form.get('message')
        
        if not recipient or not message:
            flash('Recipient and message are required.', 'danger')
            messages = []
            users = load_data('users.json')
            candidates = [u for u in users.get('users', []) if u['role'] == 'candidate']
            return render_template('admin_messages.html', messages=messages, candidates=candidates, error="Recipient and message are required.")
        
        # Construct file path for the recipient's messages
        recipient_file = f'message/{recipient}.json'
        
        # Load or create recipient's messages
        messages = load_data(recipient_file)
        new_message = {
            'sender': 'admin',
            'recipient': recipient,
            'message': message,
            'timestamp': str(datetime.now())
        }
        messages.setdefault('messages', []).append(new_message)
        save_data(recipient_file, messages)
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('admin_messages'))
    
    # Load and display messages and candidates
    messages = []
    users = load_data('users.json')
    candidates = [u for u in users.get('users', []) if u['role'] == 'candidate']
    return render_template('admin_messages.html', messages=messages, candidates=candidates)

@app.route('/admin/notifications', methods=['GET', 'POST'])
def admin_notifications():
    if 'username' not in session or not any(u['username'] == session['username'] and u['role'] == 'admin' for u in load_data('users.json')['users']):
        return redirect(url_for('login'))

    if request.method == 'POST':
        notification = request.form['notification']
        notifications = load_data('notifications.json')
        new_notification = {'notification': notification}
        notifications['notifications'].append(new_notification)
        
        save_data('notifications.json', notifications)

        return redirect(url_for('admin_notifications'))

    notifications = load_data('notifications.json')
    return render_template('admin_notifications.html', notifications=notifications['notifications'])

if __name__ == '__main__':
    app.run(debug=True)
