import sqlite3
import os

conn = sqlite3.connect('edulens.db')
cursor = conn.cursor()

cursor.executescript('''
CREATE TABLE IF NOT EXISTS students (
    student_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    age           INTEGER,
    learning_style TEXT,
    enrollment_date TEXT DEFAULT CURRENT_DATE,
    baseline_score REAL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name    TEXT NOT NULL,
    subject        TEXT,
    difficulty_level TEXT,
    total_modules  INTEGER
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER REFERENCES students(student_id),
    course_id      INTEGER REFERENCES courses(course_id),
    enrolled_on    TEXT DEFAULT CURRENT_DATE,
    progress_pct   REAL DEFAULT 0.0,
    status         TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS learning_sessions (
    session_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER REFERENCES students(student_id),
    course_id      INTEGER REFERENCES courses(course_id),
    session_start  TEXT,
    session_end    TEXT,
    duration_minutes INTEGER,
    module_number  INTEGER
);

CREATE TABLE IF NOT EXISTS cognitive_events (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     INTEGER REFERENCES learning_sessions(session_id),
    event_time     TEXT,
    state_detected TEXT,
    confidence_score REAL,
    frame_reference TEXT
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER REFERENCES students(student_id),
    course_id      INTEGER REFERENCES courses(course_id),
    taken_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    score          REAL,
    attempts       INTEGER DEFAULT 1,
    outcome        TEXT
);

CREATE TABLE IF NOT EXISTS risk_scores (
    risk_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER REFERENCES students(student_id),
    course_id      INTEGER REFERENCES courses(course_id),
    scored_on      TEXT DEFAULT CURRENT_DATE,
    dropout_probability REAL,
    risk_level     TEXT,
    trigger_factors TEXT
);

CREATE TABLE IF NOT EXISTS learning_paths (
    path_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER REFERENCES students(student_id),
    course_id      INTEGER REFERENCES courses(course_id),
    generated_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    path_type      TEXT,
    recommended_modules TEXT,
    status         TEXT DEFAULT 'active'
);
''')

conn.commit()
conn.close()

print("Database created successfully!")
print(f"File location: {os.path.abspath('edulens.db')}")
print("All 8 tables created.")
