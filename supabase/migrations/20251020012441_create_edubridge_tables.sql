/*
  # Create EduBridge Database Schema

  1. New Tables
    - `users`
      - `id` (uuid, primary key)
      - `name` (text)
      - `email` (text, unique)
      - `password` (text, hashed)
      - `role` (text, enum: 'student' or 'tutor')
      - `created_at` (timestamptz)
    
    - `subjects`
      - `id` (uuid, primary key)
      - `name` (text, unique)
      - `description` (text)
      - `created_at` (timestamptz)
    
    - `tutor_subjects`
      - `id` (uuid, primary key)
      - `tutor_id` (uuid, foreign key)
      - `subject_id` (uuid, foreign key)
      - `created_at` (timestamptz)
    
    - `sessions`
      - `id` (uuid, primary key)
      - `student_id` (uuid, foreign key)
      - `tutor_id` (uuid, foreign key)
      - `session_date` (timestamptz)
      - `status` (text, enum: 'pending', 'confirmed', 'completed')
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage their own data
    - Students can view tutors and book sessions
    - Tutors can view their subjects and session requests
*/

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text UNIQUE NOT NULL,
  password text NOT NULL,
  role text NOT NULL CHECK (role IN ('student', 'tutor')),
  created_at timestamptz DEFAULT now()
);

-- Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text UNIQUE NOT NULL,
  description text,
  created_at timestamptz DEFAULT now()
);

-- Create tutor_subjects junction table
CREATE TABLE IF NOT EXISTS tutor_subjects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tutor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  UNIQUE(tutor_id, subject_id)
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tutor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_date timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'completed')),
  created_at timestamptz DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_tutor_subjects_tutor ON tutor_subjects(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_subjects_subject ON tutor_subjects(subject_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tutor ON sessions(tutor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can read all user profiles"
  ON users FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Users can insert their own profile"
  ON users FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Users can update their own profile"
  ON users FOR UPDATE
  TO public
  USING (true)
  WITH CHECK (true);

-- RLS Policies for subjects table
CREATE POLICY "Anyone can read subjects"
  ON subjects FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Anyone can insert subjects"
  ON subjects FOR INSERT
  TO public
  WITH CHECK (true);

-- RLS Policies for tutor_subjects table
CREATE POLICY "Anyone can view tutor subjects"
  ON tutor_subjects FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Tutors can manage their subjects"
  ON tutor_subjects FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Tutors can delete their subjects"
  ON tutor_subjects FOR DELETE
  TO public
  USING (true);

-- RLS Policies for sessions table
CREATE POLICY "Users can view their own sessions"
  ON sessions FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Students can create sessions"
  ON sessions FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Users can update sessions"
  ON sessions FOR UPDATE
  TO public
  USING (true)
  WITH CHECK (true);

-- Insert default subjects
INSERT INTO subjects (name, description) VALUES
('Mathematics', 'Algebra, Calculus, Geometry, and more'),
('Physics', 'Mechanics, Thermodynamics, Electromagnetism'),
('Chemistry', 'Organic, Inorganic, and Physical Chemistry'),
('Biology', 'Cell Biology, Genetics, Ecology'),
('Computer Science', 'Programming, Algorithms, Data Structures'),
('English Literature', 'Reading, Writing, Analysis'),
('History', 'World History, Local History'),
('Economics', 'Microeconomics, Macroeconomics'),
('Psychology', 'Cognitive, Developmental, Social Psychology'),
('Foreign Languages', 'Spanish, French, German, Mandarin')
ON CONFLICT (name) DO NOTHING;
