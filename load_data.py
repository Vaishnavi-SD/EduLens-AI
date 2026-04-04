import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

db_path = r'C:\Users\vaish\OneDrive\Documents\edulens.db'
conn = sqlite3.connect(db_path)

# --- 1. Insert Courses ---
courses = [
    ('Mathematics Fundamentals', 'Mathematics', 'beginner', 10),
    ('Data Science with Python', 'Computer Science', 'intermediate', 12),
    ('Machine Learning Basics', 'Computer Science', 'advanced', 15),
    ('English Communication', 'Language', 'beginner', 8),
    ('Physics for Engineers', 'Physics', 'intermediate', 10),
]
conn.executemany('''INSERT INTO courses 
    (course_name, subject, difficulty_level, total_modules) 
    VALUES (?,?,?,?)''', courses)

# --- 2. Insert 500 Students ---
learning_styles = ['visual', 'auditory', 'reading', 'kinesthetic']
students = []
for i in range(1, 501):
    students.append((
        f'Student_{i}',
        f'student_{i}@edulens.ai',
        random.randint(18, 35),
        random.choice(learning_styles),
        round(random.uniform(40, 90), 2)
    ))
conn.executemany('''INSERT OR IGNORE INTO students 
(name, email, age, learning_style, baseline_score) 
VALUES (?,?,?,?,?)''', students)

# --- 3. Insert Enrollments ---
statuses = ['active', 'active', 'active', 'dropped', 'completed']
enrollments = []
for student_id in range(1, 501):
    course_id = random.randint(1, 5)
    enrollments.append((
        student_id,
        course_id,
        round(random.uniform(0, 100), 1),
        random.choice(statuses)
    ))
conn.executemany('''INSERT INTO enrollments 
    (student_id, course_id, progress_pct, status) 
    VALUES (?,?,?,?)''', enrollments)

# --- 4. Insert Learning Sessions ---
sessions = []
for i in range(1, 1001):
    student_id = random.randint(1, 500)
    course_id = random.randint(1, 5)
    start = datetime.now() - timedelta(days=random.randint(1, 60),
                                       hours=random.randint(0, 8))
    duration = random.randint(10, 120)
    end = start + timedelta(minutes=duration)
    sessions.append((
        student_id, course_id,
        start.strftime('%Y-%m-%d %H:%M:%S'),
        end.strftime('%Y-%m-%d %H:%M:%S'),
        duration,
        random.randint(1, 10)
    ))
conn.executemany('''INSERT INTO learning_sessions 
    (student_id, course_id, session_start, session_end, 
     duration_minutes, module_number) 
    VALUES (?,?,?,?,?,?)''', sessions)

# --- 5. Insert Assessments ---
assessments = []
for student_id in range(1, 501):
    course_id = random.randint(1, 5)
    score = round(random.uniform(20, 100), 1)
    assessments.append((
        student_id, course_id, score,
        'pass' if score >= 40 else 'fail'
    ))
conn.executemany('''INSERT INTO assessments 
    (student_id, course_id, score, outcome) 
    VALUES (?,?,?,?)''', assessments)

# --- 6. Insert Risk Scores ---
risk_levels = ['low', 'medium', 'high', 'critical']
risks = []
for student_id in range(1, 501):
    course_id = random.randint(1, 5)
    prob = round(random.uniform(0, 1), 2)
    if prob < 0.3:
        level = 'low'
    elif prob < 0.6:
        level = 'medium'
    elif prob < 0.8:
        level = 'high'
    else:
        level = 'critical'
    risks.append((student_id, course_id, prob, level))
conn.executemany('''INSERT INTO risk_scores 
    (student_id, course_id, dropout_probability, risk_level) 
    VALUES (?,?,?,?)''', risks)

conn.commit()

# --- Verify ---
tables = ['students','courses','enrollments',
          'learning_sessions','assessments','risk_scores']
print("\nData loaded successfully!")
print("-" * 35)
for t in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    print(f"{t:25s}: {count} rows")

conn.close()