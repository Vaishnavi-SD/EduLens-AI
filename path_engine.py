import pandas as pd
import numpy as np
import sqlite3
import pickle
import json
from datetime import datetime

print("=" * 50)
print("EduLens AI — Personalized Learning Path Engine")
print("=" * 50)

db_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\edulens.db'
model_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\dropout_model.pkl'
encoder_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\label_encoder.pkl'

conn = sqlite3.connect(db_path)
with open(model_path, 'rb') as f:
    model = pickle.load(f)
with open(encoder_path, 'rb') as f:
    le = pickle.load(f)

print("\nModel and database loaded!")

# ================================================
#  Load student data
# ================================================
query = '''
SELECT 
    s.student_id, s.name, s.age, s.baseline_score, s.learning_style,
    e.course_id, e.progress_pct, e.status,
    c.course_name, c.subject, c.total_modules
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE e.status = 'active'
LIMIT 20
'''
students_df = pd.read_sql(query, conn)
print(f"\nLoaded {len(students_df)} active students for analysis")

# ================================================
#  Build features for prediction
# ================================================
risk_df = pd.read_sql('SELECT * FROM risk_scores', conn)
assess_df = pd.read_sql('SELECT * FROM assessments', conn)
session_df = pd.read_sql('SELECT * FROM learning_sessions', conn)

avg_score = assess_df.groupby('student_id')['score'].agg(
    avg_score='mean', failed_count=lambda x: (x < 40).sum()
).reset_index()

avg_session = session_df.groupby('student_id')['duration_minutes'].agg(
    avg_duration='mean', total_sessions='count'
).reset_index()

features_df = students_df.merge(avg_score, on='student_id', how='left')
features_df = features_df.merge(avg_session, on='student_id', how='left')
features_df = features_df.merge(
    risk_df[['student_id', 'dropout_probability', 'risk_level']],
    on='student_id', how='left'
)

features_df.fillna({
    'avg_score': 50, 'failed_count': 0,
    'avg_duration': 30, 'total_sessions': 1,
    'dropout_probability': 0.3, 'risk_level': 'low'
}, inplace=True)

risk_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
features_df['risk_level_encoded'] = features_df['risk_level'].map(risk_map).fillna(0)
features_df['learning_style_encoded'] = features_df['learning_style'].apply(
    lambda x: le.transform([x])[0] if x in le.classes_ else 0
)

FEATURES = [
    'age', 'baseline_score', 'progress_pct',
    'avg_duration', 'total_sessions', 'avg_score',
    'failed_count', 'dropout_probability',
    'learning_style_encoded', 'risk_level_encoded'
]

X = features_df[FEATURES]
features_df['dropout_pred'] = model.predict(X)
features_df['dropout_prob'] = model.predict_proba(X)[:, 1]

# ================================================
# Path generation engine
# ================================================
def generate_learning_path(student):
    prob = student['dropout_prob']
    style = student['learning_style']
    score = student['avg_score']
    progress = student['progress_pct']
    total_modules = int(student['total_modules'])
    course_name = student['course_name']

    # Determine path type
    if prob >= 0.5:
        path_type = 'CRITICAL INTERVENTION'
        urgency = 'Immediate action required'
    elif prob >= 0.3:
        path_type = 'REMEDIAL'
        urgency = 'Extra support needed'
    elif prob >= 0.15:
        path_type = 'SUPPORTIVE'
        urgency = 'Monitor closely'
    else:
        path_type = 'STANDARD'
        urgency = 'On track'

    # Learning style recommendations
    style_tips = {
        'visual': [
            'Watch video summaries for each module',
            'Use mind maps to connect concepts',
            'Review diagram-based study materials'
        ],
        'auditory': [
            'Listen to recorded lectures',
            'Join study discussion groups',
            'Use text-to-speech for reading material'
        ],
        'reading': [
            'Read module summaries before starting',
            'Take structured notes for each topic',
            'Use flashcards for key concepts'
        ],
        'kinesthetic': [
            'Work through hands-on practice problems',
            'Build mini-projects for each module',
            'Use interactive simulations'
        ]
    }

    # Generate recommended modules based on progress
    current_module = max(1, int((progress / 100) * total_modules))
    if path_type in ['CRITICAL INTERVENTION', 'REMEDIAL']:
        # Go back and redo weak modules
        start = max(1, current_module - 2)
        recommended = list(range(start, min(start + 5, total_modules + 1)))
    else:
        # Continue forward
        recommended = list(range(current_module, min(current_module + 3, total_modules + 1)))

    tips = style_tips.get(style, style_tips['reading'])

    return {
        'path_type': path_type,
        'urgency': urgency,
        'dropout_probability': f"{prob * 100:.1f}%",
        'recommended_modules': recommended,
        'learning_tips': tips,
        'weekly_goal': f"Complete {len(recommended)} modules in 7 days",
        'course': course_name
    }

# ================================================
#  Generate paths for at-risk students
# ================================================
at_risk = features_df[features_df['dropout_prob'] >= 0.1].copy()
print(f"\nStudents needing intervention: {len(at_risk)}")

paths_generated = []
for _, student in at_risk.iterrows():
    path = generate_learning_path(student)
    path['student_id'] = int(student['student_id'])
    path['student_name'] = student['name']
    paths_generated.append(path)

    # Save to database
    conn.execute('''
        INSERT INTO learning_paths 
        (student_id, course_id, path_type, recommended_modules, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        int(student['student_id']),
        int(student['course_id']),
        path['path_type'],
        json.dumps(path['recommended_modules']),
        'active'
    ))

conn.commit()

# ================================================
#  Print sample paths
# ================================================
print("\n" + "=" * 50)
print("SAMPLE GENERATED LEARNING PATHS")
print("=" * 50)

for path in paths_generated[:5]:
    print(f"\nStudent: {path['student_name']} (ID: {path['student_id']})")
    print(f"Course:  {path['course']}")
    print(f"Status:  {path['path_type']} — {path['urgency']}")
    print(f"Dropout risk: {path['dropout_probability']}")
    print(f"Recommended modules: {path['recommended_modules']}")
    print(f"Weekly goal: {path['weekly_goal']}")
    print(f"Learning tips:")
    for tip in path['learning_tips']:
        print(f"  - {tip}")
    print("-" * 40)

# ================================================
#  Summary stats
# ================================================
path_type_counts = {}
for p in paths_generated:
    pt = p['path_type']
    path_type_counts[pt] = path_type_counts.get(pt, 0) + 1

print("\n" + "=" * 50)
print("PATH GENERATION SUMMARY")
print("=" * 50)
total = len(paths_generated)
for pt, count in sorted(path_type_counts.items()):
    print(f"{pt:30s}: {count} students ({count/total*100:.1f}%)")

# Save all paths to JSON for the dashboard
import os
output_path = 'learning_paths.json'
with open(output_path, 'w') as f:
    json.dump(paths_generated, f, indent=2)

print(f"\nAll paths saved to learning_paths.json")
print(f"Paths saved to database: {total} records")

conn.close()

print("\n" + "=" * 50)
print("Personalized Learning Path Engine is live.")
print("=" * 50)
