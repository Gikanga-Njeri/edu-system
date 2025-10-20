# EduBridge - Quality Education Platform

EduBridge is a Flask-based web application that connects students with tutors to support learning and mentorship. Inspired by UN Sustainable Development Goal 4: Quality Education.

## Features

### Authentication & User Management
- Register as a student or tutor with secure password encryption (bcrypt)
- Role-based authentication with Flask-Login
- Automatic redirection based on user role

### Student Features
- Search for tutors by subject or name
- View tutor profiles with their expertise
- Book study sessions with tutors
- Track session status (pending, confirmed, completed)

### Tutor Features
- Add and manage subjects they teach
- View and manage session requests from students
- Confirm or complete session bookings
- Professional dashboard to track all activities

### UI/UX
- Modern Bootstrap 5 interface
- Responsive design for all devices
- Flash messages for user feedback
- Clean, intuitive navigation

## Tech Stack

- **Backend**: Flask (Python 3.x)
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Authentication**: Flask-Login + bcrypt
- **Database Connector**: Flask-MySQLdb

## Project Structure

```
edubridge/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Home page
│   ├── register.html          # Registration page
│   ├── login.html             # Login page
│   ├── dashboard_student.html # Student dashboard
│   └── dashboard_tutor.html   # Tutor dashboard
└── static/
    ├── css/
    │   └── style.css          # Custom styles
    └── js/                    # JavaScript files
```

## Database Schema

### users
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- name (VARCHAR(100))
- email (VARCHAR(100), UNIQUE)
- password (VARCHAR(255))
- role (ENUM: 'student', 'tutor')
- created_at (TIMESTAMP)

### subjects
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- name (VARCHAR(100), UNIQUE)
- description (TEXT)
- created_at (TIMESTAMP)

### tutor_subjects
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- tutor_id (INT, FOREIGN KEY)
- subject_id (INT, FOREIGN KEY)
- created_at (TIMESTAMP)

### sessions
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- student_id (INT, FOREIGN KEY)
- tutor_id (INT, FOREIGN KEY)
- date (DATETIME)
- status (ENUM: 'pending', 'confirmed', 'completed')
- created_at (TIMESTAMP)

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd edubridge
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up MySQL Database
```bash
# Login to MySQL
mysql -u root -p

# Create database and import schema
mysql -u root -p < schema.sql
```

### Step 5: Configure Environment Variables
Create a `.env` file in the project root (or update config.py):
```
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=edubridge
```

### Step 6: Run the Application
```bash
flask run
```

Or:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage Guide

### For Students
1. Register an account and select "Student" as your role
2. Log in with your credentials
3. Search for tutors by subject or name
4. Click "Book Session" on a tutor's card
5. Select date and time for your session
6. Track your sessions in the "My Sessions" section

### For Tutors
1. Register an account and select "Tutor" as your role
2. Log in with your credentials
3. Add subjects you can teach from the dropdown
4. View and manage session requests from students
5. Confirm sessions or mark them as completed

## Default Subjects

The database comes pre-populated with these subjects:
- Mathematics
- Physics
- Chemistry
- Biology
- Computer Science
- English Literature
- History
- Economics
- Psychology
- Foreign Languages

## Security Features

- Password hashing with bcrypt
- Session management with Flask-Login
- Role-based access control
- SQL injection prevention with parameterized queries
- CSRF protection (Flask default)

## Development

### Running in Debug Mode
```bash
export FLASK_ENV=development  # On macOS/Linux
set FLASK_ENV=development     # On Windows
flask run
```

### Database Migrations
To modify the database schema, update `schema.sql` and re-run:
```bash
mysql -u root -p edubridge < schema.sql
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please open an issue on the GitHub repository.

## Acknowledgments

- Inspired by UN SDG 4: Quality Education
- Built with Flask and Bootstrap
- Community contributors

---

**EduBridge** - Connecting learners and educators for a better tomorrow.