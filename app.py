from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from functools import wraps
from datetime import datetime
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ---------------------- MODELS ----------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(10))  # student or tutor


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)


class TutorSubject(db.Model):
    __tablename__ = 'tutor_subjects'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')


# Create all tables
with app.app_context():
    db.create_all()


# ---------------------- LOGIN HANDLER ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


# ---------------------- ROUTES ----------------------

@app.route('/')
def index():
    return render_template('index.html')


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.', 'danger')
            return render_template('register.html')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')

            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('tutor_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


# ---------- STUDENT DASHBOARD ----------
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    search = request.args.get('search', '')

    tutors = User.query.filter_by(role='tutor').all()
    results = []

    for tutor in tutors:
        tutor_subjects = TutorSubject.query.filter_by(tutor_id=tutor.id).all()
        subject_ids = [ts.subject_id for ts in tutor_subjects]
        subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
        subject_names = ', '.join([s.name for s in subjects])

        if not search or (search.lower() in tutor.name.lower() or search.lower() in subject_names.lower()):
            results.append({'id': tutor.id, 'name': tutor.name, 'email': tutor.email, 'subjects': subject_names})

    my_sessions = Session.query.filter_by(student_id=current_user.id).all()

    return render_template('dashboard_student.html', tutors=results, my_sessions=my_sessions, search=search)


# ---------- BOOK SESSION ----------
@app.route('/student/book_session/<int:tutor_id>', methods=['POST'])
@login_required
@role_required('student')
def book_session(tutor_id):
    session_date = request.form['session_date']
    session_date_obj = datetime.strptime(session_date, '%Y-%m-%dT%H:%M')

    new_session = Session(student_id=current_user.id, tutor_id=tutor_id, session_date=session_date_obj)
    db.session.add(new_session)
    db.session.commit()

    flash('Session request sent successfully!', 'success')
    return redirect(url_for('student_dashboard'))


# ---------- TUTOR DASHBOARD ----------
@app.route('/tutor/dashboard')
@login_required
@role_required('tutor')
def tutor_dashboard():
    my_subjects = TutorSubject.query.filter_by(tutor_id=current_user.id).all()
    subject_ids = [ts.subject_id for ts in my_subjects]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()

    all_subjects = Subject.query.all()
    session_requests = Session.query.filter_by(tutor_id=current_user.id).all()

    return render_template('dashboard_tutor.html',
                           my_subjects=subjects,
                           all_subjects=all_subjects,
                           session_requests=session_requests)


# ---------- ADD SUBJECT ----------
@app.route('/tutor/add_subject', methods=['POST'])
@login_required
@role_required('tutor')
def add_subject():
    subject_id = request.form['subject_id']

    existing = TutorSubject.query.filter_by(tutor_id=current_user.id, subject_id=subject_id).first()
    if existing:
        flash('Subject already added.', 'danger')
    else:
        new_tutor_subject = TutorSubject(tutor_id=current_user.id, subject_id=subject_id)
        db.session.add(new_tutor_subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')

    return redirect(url_for('tutor_dashboard'))


# ---------- REMOVE SUBJECT ----------
@app.route('/tutor/remove_subject/<int:subject_id>')
@login_required
@role_required('tutor')
def remove_subject(subject_id):
    TutorSubject.query.filter_by(tutor_id=current_user.id, subject_id=subject_id).delete()
    db.session.commit()
    flash('Subject removed successfully!', 'success')
    return redirect(url_for('tutor_dashboard'))


# ---------- UPDATE SESSION STATUS ----------
@app.route('/tutor/update_session/<int:session_id>/<status>')
@login_required
@role_required('tutor')
def update_session(session_id, status):
    if status not in ['confirmed', 'completed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('tutor_dashboard'))

    session = Session.query.filter_by(id=session_id, tutor_id=current_user.id).first()
    if session:
        session.status = status
        db.session.commit()
        flash(f'Session {status} successfully!', 'success')
    else:
        flash('Session not found.', 'danger')

    return redirect(url_for('tutor_dashboard'))


# ---------------------- RUN APP ----------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
