import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os

db_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\edulens.db'
conn = sqlite3.connect(db_path)

print("=" * 50)
print("EduLens AI — Exploratory Data Analysis")
print("=" * 50)

# --- Load all tables ---
students     = pd.read_sql('SELECT * FROM students', conn)
enrollments  = pd.read_sql('SELECT * FROM enrollments', conn)
assessments  = pd.read_sql('SELECT * FROM assessments', conn)
sessions     = pd.read_sql('SELECT * FROM learning_sessions', conn)
risk         = pd.read_sql('SELECT * FROM risk_scores', conn)

# ================================================
# ANALYSIS 1: Dropout Rate
# ================================================
print("\n--- Enrollment Status Breakdown ---")
status_counts = enrollments['status'].value_counts()
print(status_counts)
dropout_rate = (status_counts.get('dropped', 0) / len(enrollments)) * 100
print(f"\nDropout Rate: {dropout_rate:.1f}%")

# ================================================
# ANALYSIS 2: Score Distribution
# ================================================
print("\n--- Assessment Score Stats ---")
print(assessments['score'].describe().round(2))

# ================================================
# ANALYSIS 3: Risk Level Distribution
# ================================================
print("\n--- Risk Level Distribution ---")
print(risk['risk_level'].value_counts())

# ================================================
# ANALYSIS 4: Feature Engineering
# Build the master ML dataset
# ================================================
print("\n--- Building ML Feature Dataset ---")

# Average session duration per student
avg_session = sessions.groupby('student_id')['duration_minutes'].agg(
    avg_duration='mean',
    total_sessions='count'
).reset_index()

# Average score per student
avg_score = assessments.groupby('student_id')['score'].agg(
    avg_score='mean',
    failed_count=lambda x: (x < 40).sum()
).reset_index()

# Merge everything
ml_data = enrollments[['student_id', 'course_id', 'progress_pct', 'status']].copy()
ml_data = ml_data.merge(students[['student_id', 'age', 'baseline_score', 'learning_style']], on='student_id', how='left')
ml_data = ml_data.merge(avg_session, on='student_id', how='left')
ml_data = ml_data.merge(avg_score, on='student_id', how='left')
ml_data = ml_data.merge(risk[['student_id', 'dropout_probability', 'risk_level']], on='student_id', how='left')

# Create target label: 1 = dropped, 0 = active/completed
ml_data['dropout_label'] = (ml_data['status'] == 'dropped').astype(int)

# Fill missing values
ml_data.fillna({
    'avg_duration': 0,
    'total_sessions': 0,
    'avg_score': 0,
    'failed_count': 0
}, inplace=True)

print(f"\nML Dataset shape: {ml_data.shape}")
print(f"Features: {list(ml_data.columns)}")
print(f"\nDropout cases: {ml_data['dropout_label'].sum()}")
print(f"Non-dropout cases: {(ml_data['dropout_label'] == 0).sum()}")

# Save ML dataset
ml_data.to_csv(r'C:\Users\vaish\OneDrive\Documents\AiProject\ml_dataset.csv', index=False)
print("\nML dataset saved as ml_dataset.csv")

# ================================================
# CHARTS — Save all as PNG files
# ================================================
output_dir = r'C:\Users\vaish\OneDrive\Documents\AiProject\charts'
os.makedirs(output_dir, exist_ok=True)

sns.set_theme(style='whitegrid')
colors = ['#378ADD', '#1D9E75', '#E24B4A', '#BA7517']

# Chart 1: Dropout Rate Pie Chart
fig, ax = plt.subplots(figsize=(6, 5))
status_counts.plot.pie(
    ax=ax, autopct='%1.1f%%',
    colors=colors[:len(status_counts)],
    startangle=90
)
ax.set_title('Enrollment Status Distribution', fontsize=14)
ax.set_ylabel('')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '1_dropout_rate.png'), dpi=150)
plt.close()
print("Chart 1 saved: dropout rate")

# Chart 2: Score Distribution
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(assessments['score'], bins=20, color='#378ADD', ax=ax, kde=True)
ax.axvline(x=40, color='red', linestyle='--', label='Pass threshold (40)')
ax.set_title('Assessment Score Distribution', fontsize=14)
ax.set_xlabel('Score')
ax.set_ylabel('Number of Students')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '2_score_distribution.png'), dpi=150)
plt.close()
print("Chart 2 saved: score distribution")

# Chart 3: Risk Level Bar Chart
fig, ax = plt.subplots(figsize=(7, 5))
risk_counts = risk['risk_level'].value_counts()
risk_order = ['low', 'medium', 'high', 'critical']
risk_counts = risk_counts.reindex([r for r in risk_order if r in risk_counts.index])
bars = ax.bar(risk_counts.index, risk_counts.values,
              color=['#1D9E75', '#BA7517', '#E24B4A', '#7F77DD'])
ax.set_title('Student Risk Level Distribution', fontsize=14)
ax.set_xlabel('Risk Level')
ax.set_ylabel('Number of Students')
for bar, val in zip(bars, risk_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
            str(val), ha='center', fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '3_risk_levels.png'), dpi=150)
plt.close()
print("Chart 3 saved: risk levels")

# Chart 4: Session Duration vs Score
fig, ax = plt.subplots(figsize=(8, 5))
plot_data = ml_data[ml_data['avg_duration'] > 0]
scatter = ax.scatter(
    plot_data['avg_duration'],
    plot_data['avg_score'],
    c=plot_data['dropout_label'],
    cmap='RdYlGn_r', alpha=0.6, s=50
)
plt.colorbar(scatter, ax=ax, label='Dropout (1=Yes)')
ax.set_title('Session Duration vs Score (colored by dropout)', fontsize=13)
ax.set_xlabel('Average Session Duration (mins)')
ax.set_ylabel('Average Score')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '4_duration_vs_score.png'), dpi=150)
plt.close()
print("Chart 4 saved: duration vs score")

# Chart 5: Correlation Heatmap
fig, ax = plt.subplots(figsize=(9, 7))
numeric_cols = ['age', 'baseline_score', 'progress_pct',
                'avg_duration', 'total_sessions',
                'avg_score', 'dropout_probability', 'dropout_label']
corr = ml_data[numeric_cols].corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            ax=ax, square=True, linewidths=0.5)
ax.set_title('Feature Correlation Heatmap', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, '5_correlation_heatmap.png'), dpi=150)
plt.close()
print("Chart 5 saved: correlation heatmap")

conn.close()
print("\n" + "=" * 50)
print("Week 2 EDA COMPLETE!")
print(f"All charts saved in: {output_dir}")
print("Next step: Week 3 — Train the dropout prediction model")
print("=" * 50)