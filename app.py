from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from functools import wraps
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
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
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        return User(user_data['id'], user_data['name'], user_data['email'], user_data['role'])
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

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                       (name, email, hashed_password, role))
            mysql.connection.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Email already exists or registration failed.', 'danger')
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cur.fetchone()
        cur.close()

        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            user = User(user_data['id'], user_data['name'], user_data['email'], user_data['role'])
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')

            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('tutor_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

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

    cur = mysql.connection.cursor()

    if search:
        cur.execute("""
            SELECT DISTINCT u.id, u.name, u.email, GROUP_CONCAT(s.name SEPARATOR ', ') as subjects
            FROM users u
            JOIN tutor_subjects ts ON u.id = ts.tutor_id
            JOIN subjects s ON ts.subject_id = s.id
            WHERE u.role = 'tutor' AND (u.name LIKE %s OR s.name LIKE %s)
            GROUP BY u.id, u.name, u.email
        """, (f'%{search}%', f'%{search}%'))
    else:
        cur.execute("""
            SELECT u.id, u.name, u.email, GROUP_CONCAT(s.name SEPARATOR ', ') as subjects
            FROM users u
            JOIN tutor_subjects ts ON u.id = ts.tutor_id
            JOIN subjects s ON ts.subject_id = s.id
            WHERE u.role = 'tutor'
            GROUP BY u.id, u.name, u.email
        """)

    tutors = cur.fetchall()

    cur.execute("""
        SELECT ses.*, u.name as tutor_name
        FROM sessions ses
        JOIN users u ON ses.tutor_id = u.id
        WHERE ses.student_id = %s
        ORDER BY ses.date DESC
    """, (current_user.id,))
    my_sessions = cur.fetchall()

    cur.close()

    return render_template('dashboard_student.html', tutors=tutors, my_sessions=my_sessions, search=search)

@app.route('/student/book_session/<int:tutor_id>', methods=['POST'])
@login_required
@role_required('student')
def book_session(tutor_id):
    session_date = request.form['session_date']

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO sessions (student_id, tutor_id, date, status)
            VALUES (%s, %s, %s, 'pending')
        """, (current_user.id, tutor_id, session_date))
        mysql.connection.commit()
        flash('Session request sent successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to book session. Please try again.', 'danger')
    finally:
        cur.close()

    return redirect(url_for('student_dashboard'))

@app.route('/tutor/dashboard')
@login_required
@role_required('tutor')
def tutor_dashboard():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT s.id, s.name, s.description
        FROM subjects s
        JOIN tutor_subjects ts ON s.id = ts.subject_id
        WHERE ts.tutor_id = %s
    """, (current_user.id,))
    my_subjects = cur.fetchall()

    cur.execute("SELECT * FROM subjects")
    all_subjects = cur.fetchall()

    cur.execute("""
        SELECT ses.*, u.name as student_name, u.email as student_email
        FROM sessions ses
        JOIN users u ON ses.student_id = u.id
        WHERE ses.tutor_id = %s
        ORDER BY ses.date DESC
    """, (current_user.id,))
    session_requests = cur.fetchall()

    cur.close()

    return render_template('dashboard_tutor.html',
                         my_subjects=my_subjects,
                         all_subjects=all_subjects,
                         session_requests=session_requests)

@app.route('/tutor/add_subject', methods=['POST'])
@login_required
@role_required('tutor')
def add_subject():
    subject_id = request.form['subject_id']

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO tutor_subjects (tutor_id, subject_id)
            VALUES (%s, %s)
        """, (current_user.id, subject_id))
        mysql.connection.commit()
        flash('Subject added successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash('Subject already added or operation failed.', 'danger')
    finally:
        cur.close()

    return redirect(url_for('tutor_dashboard'))

@app.route('/tutor/remove_subject/<int:subject_id>')
@login_required
@role_required('tutor')
def remove_subject(subject_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            DELETE FROM tutor_subjects
            WHERE tutor_id = %s AND subject_id = %s
        """, (current_user.id, subject_id))
        mysql.connection.commit()
        flash('Subject removed successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to remove subject.', 'danger')
    finally:
        cur.close()

    return redirect(url_for('tutor_dashboard'))

@app.route('/tutor/update_session/<int:session_id>/<status>')
@login_required
@role_required('tutor')
def update_session(session_id, status):
    if status not in ['confirmed', 'completed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('tutor_dashboard'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            UPDATE sessions
            SET status = %s
            WHERE id = %s AND tutor_id = %s
        """, (status, session_id, current_user.id))
        mysql.connection.commit()
        flash(f'Session {status} successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to update session.', 'danger')
    finally:
        cur.close()

    return redirect(url_for('tutor_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
