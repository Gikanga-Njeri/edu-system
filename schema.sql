-- EduBridge Database Schema
-- Drop database if exists and create fresh
DROP DATABASE IF EXISTS edubridge;
CREATE DATABASE edubridge;
USE edubridge;

-- Users table
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role ENUM('student','tutor') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table
CREATE TABLE subjects (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tutor subjects junction table
CREATE TABLE tutor_subjects (
  id INT PRIMARY KEY AUTO_INCREMENT,
  tutor_id INT NOT NULL,
  subject_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tutor_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  UNIQUE KEY unique_tutor_subject (tutor_id, subject_id)
);

-- Sessions table
CREATE TABLE sessions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_id INT NOT NULL,
  tutor_id INT NOT NULL,
  date DATETIME NOT NULL,
  status ENUM('pending','confirmed','completed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (tutor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert sample subjects
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
('Foreign Languages', 'Spanish, French, German, Mandarin');

-- Create indexes for better performance
CREATE INDEX idx_tutor_subjects_tutor ON tutor_subjects(tutor_id);
CREATE INDEX idx_tutor_subjects_subject ON tutor_subjects(subject_id);
CREATE INDEX idx_sessions_student ON sessions(student_id);
CREATE INDEX idx_sessions_tutor ON sessions(tutor_id);
CREATE INDEX idx_sessions_status ON sessions(status);
