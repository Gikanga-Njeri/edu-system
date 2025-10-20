from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from functools import wraps
from config import Config
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)
app.config.from_object(Config)

supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            user_data = response.data[0]
            return User(user_data['id'], user_data['name'], user_data['email'], user_data['role'])
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied. You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            existing = supabase.table('users').select('email').eq('email', email).execute()
            if existing.data:
                flash('Email already exists.', 'danger')
                return render_template('register.html')

            supabase.table('users').insert({
                'name': name,
                'email': email,
                'password': hashed_password,
                'role': role
            }).execute()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {e}")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            response = supabase.table('users').select('*').eq('email', email).execute()

            if response.data:
                user_data = response.data[0]
                if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
                    user = User(user_data['id'], user_data['name'], user_data['email'], user_data['role'])
                    login_user(user)
                    flash(f'Welcome back, {user.name}!', 'success')

                    if user.role == 'student':
                        return redirect(url_for('student_dashboard'))
                    else:
                        return redirect(url_for('tutor_dashboard'))

            flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash('Login failed. Please try again.', 'danger')
            print(f"Login error: {e}")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    search = request.args.get('search', '')

    try:
        if search:
            tutors_response = supabase.table('users').select('id, name, email').eq('role', 'tutor').execute()
            tutors = []

            for tutor in tutors_response.data:
                tutor_subjects_response = supabase.table('tutor_subjects').select('subject_id').eq('tutor_id', tutor['id']).execute()
                subject_ids = [ts['subject_id'] for ts in tutor_subjects_response.data]

                if subject_ids:
                    subjects_response = supabase.table('subjects').select('name').in_('id', subject_ids).execute()
                    subject_names = ', '.join([s['name'] for s in subjects_response.data])

                    if search.lower() in tutor['name'].lower() or search.lower() in subject_names.lower():
                        tutor['subjects'] = subject_names
                        tutors.append(tutor)
        else:
            tutors_response = supabase.table('users').select('id, name, email').eq('role', 'tutor').execute()
            tutors = []

            for tutor in tutors_response.data:
                tutor_subjects_response = supabase.table('tutor_subjects').select('subject_id').eq('tutor_id', tutor['id']).execute()
                subject_ids = [ts['subject_id'] for ts in tutor_subjects_response.data]

                if subject_ids:
                    subjects_response = supabase.table('subjects').select('name').in_('id', subject_ids).execute()
                    tutor['subjects'] = ', '.join([s['name'] for s in subjects_response.data])
                    tutors.append(tutor)

        sessions_response = supabase.table('sessions').select('*').eq('student_id', current_user.id).execute()
        my_sessions = []

        for session in sessions_response.data:
            tutor_response = supabase.table('users').select('name').eq('id', session['tutor_id']).execute()
            if tutor_response.data:
                session['tutor_name'] = tutor_response.data[0]['name']
                session['date'] = datetime.fromisoformat(session['session_date'].replace('Z', '+00:00'))
                my_sessions.append(session)

    except Exception as e:
        print(f"Dashboard error: {e}")
        tutors = []
        my_sessions = []

    return render_template('dashboard_student.html', tutors=tutors, my_sessions=my_sessions, search=search)

@app.route('/student/book_session/<tutor_id>', methods=['POST'])
@login_required
@role_required('student')
def book_session(tutor_id):
    session_date = request.form['session_date']

    try:
        supabase.table('sessions').insert({
            'student_id': current_user.id,
            'tutor_id': tutor_id,
            'session_date': session_date,
            'status': 'pending'
        }).execute()

        flash('Session request sent successfully!', 'success')
    except Exception as e:
        flash('Failed to book session. Please try again.', 'danger')
        print(f"Booking error: {e}")

    return redirect(url_for('student_dashboard'))

@app.route('/tutor/dashboard')
@login_required
@role_required('tutor')
def tutor_dashboard():
    try:
        tutor_subjects_response = supabase.table('tutor_subjects').select('subject_id').eq('tutor_id', current_user.id).execute()
        subject_ids = [ts['subject_id'] for ts in tutor_subjects_response.data]

        my_subjects = []
        if subject_ids:
            subjects_response = supabase.table('subjects').select('*').in_('id', subject_ids).execute()
            my_subjects = subjects_response.data

        all_subjects_response = supabase.table('subjects').select('*').execute()
        all_subjects = all_subjects_response.data

        sessions_response = supabase.table('sessions').select('*').eq('tutor_id', current_user.id).execute()
        session_requests = []

        for session in sessions_response.data:
            student_response = supabase.table('users').select('name, email').eq('id', session['student_id']).execute()
            if student_response.data:
                session['student_name'] = student_response.data[0]['name']
                session['student_email'] = student_response.data[0]['email']
                session['date'] = datetime.fromisoformat(session['session_date'].replace('Z', '+00:00'))
                session_requests.append(session)

    except Exception as e:
        print(f"Tutor dashboard error: {e}")
        my_subjects = []
        all_subjects = []
        session_requests = []

    return render_template('dashboard_tutor.html',
                         my_subjects=my_subjects,
                         all_subjects=all_subjects,
                         session_requests=session_requests)

@app.route('/tutor/add_subject', methods=['POST'])
@login_required
@role_required('tutor')
def add_subject():
    subject_id = request.form['subject_id']

    try:
        existing = supabase.table('tutor_subjects').select('*').eq('tutor_id', current_user.id).eq('subject_id', subject_id).execute()

        if existing.data:
            flash('Subject already added.', 'danger')
        else:
            supabase.table('tutor_subjects').insert({
                'tutor_id': current_user.id,
                'subject_id': subject_id
            }).execute()
            flash('Subject added successfully!', 'success')
    except Exception as e:
        flash('Failed to add subject.', 'danger')
        print(f"Add subject error: {e}")

    return redirect(url_for('tutor_dashboard'))

@app.route('/tutor/remove_subject/<subject_id>')
@login_required
@role_required('tutor')
def remove_subject(subject_id):
    try:
        supabase.table('tutor_subjects').delete().eq('tutor_id', current_user.id).eq('subject_id', subject_id).execute()
        flash('Subject removed successfully!', 'success')
    except Exception as e:
        flash('Failed to remove subject.', 'danger')
        print(f"Remove subject error: {e}")

    return redirect(url_for('tutor_dashboard'))

@app.route('/tutor/update_session/<session_id>/<status>')
@login_required
@role_required('tutor')
def update_session(session_id, status):
    if status not in ['confirmed', 'completed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('tutor_dashboard'))

    try:
        supabase.table('sessions').update({'status': status}).eq('id', session_id).eq('tutor_id', current_user.id).execute()
        flash(f'Session {status} successfully!', 'success')
    except Exception as e:
        flash('Failed to update session.', 'danger')
        print(f"Update session error: {e}")

    return redirect(url_for('tutor_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
