import pandas as pd
import numpy as np
import sqlite3
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, roc_auc_score, roc_curve)
from xgboost import XGBClassifier

print("=" * 50)
print("EduLens AI — Dropout Prediction Model")
print("=" * 50)

# ================================================
# Load ML Dataset
# ================================================
df = pd.read_csv(r'C:\Users\vaish\OneDrive\Documents\AiProject\ml_dataset.csv')
print(f"\nDataset loaded: {df.shape[0]} students, {df.shape[1]} features")

# ================================================
# Prepare Features
# ================================================
# Encode learning_style (text → number)
le = LabelEncoder()
df['learning_style_encoded'] = le.fit_transform(df['learning_style'].fillna('unknown'))

# Encode risk_level
risk_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
df['risk_level_encoded'] = df['risk_level'].map(risk_map).fillna(0)

# Select final features for the model
FEATURES = [
    'age',
    'baseline_score',
    'progress_pct',
    'avg_duration',
    'total_sessions',
    'avg_score',
    'failed_count',
    'dropout_probability',
    'learning_style_encoded',
    'risk_level_encoded'
]

TARGET = 'dropout_label'

X = df[FEATURES]
y = df[TARGET]

print(f"\nFeatures used: {FEATURES}")
print(f"Target: {TARGET}")
print(f"\nClass distribution:")
print(y.value_counts())

# ================================================
# Split Data
# ================================================
from imblearn.over_sampling import SMOTE

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

smote = SMOTE(random_state=42)
X_train, y_train = smote.fit_resample(X_train, y_train)
print(f"\nAfter SMOTE balancing:")
print(f"Training set: {len(X_train)} students (balanced)")
print(f"\nTraining set: {X_train.shape[0]} students")
print(f"Test set:     {X_test.shape[0]} students")

# ================================================
# Train XGBoost Model
# ================================================
print("\nTraining XGBoost model...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    scale_pos_weight=3,
    eval_metric='logloss',
    random_state=42
)

model.fit(X_train, y_train)
print("Model trained!")

# ================================================
# Evaluate
# ================================================
y_pred      = model.predict(X_test)
y_pred_prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
roc_auc  = roc_auc_score(y_test, y_pred_prob)

print("\n" + "=" * 50)
print("MODEL PERFORMANCE")
print("=" * 50)
print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"ROC-AUC:   {roc_auc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred,
      target_names=['Not Dropout', 'Dropout']))

# ================================================
# Save Charts
# ================================================
import os
charts_dir = r'C:\Users\vaish\OneDrive\Documents\AiProject\charts'
os.makedirs(charts_dir, exist_ok=True)

sns.set_theme(style='whitegrid')

# Chart 6: Confusion Matrix
fig, ax = plt.subplots(figsize=(6, 5))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Not Dropout', 'Dropout'],
            yticklabels=['Not Dropout', 'Dropout'])
ax.set_title(f'Confusion Matrix (Accuracy: {accuracy*100:.1f}%)', fontsize=13)
ax.set_ylabel('Actual')
ax.set_xlabel('Predicted')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '6_confusion_matrix.png'), dpi=150)
plt.close()
print("\nChart 6 saved: confusion matrix")

# Chart 7: ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_pred_prob)
fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(fpr, tpr, color='#378ADD', lw=2,
        label=f'ROC Curve (AUC = {roc_auc:.3f})')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random')
ax.set_title('ROC Curve — Dropout Prediction Model', fontsize=13)
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '7_roc_curve.png'), dpi=150)
plt.close()
print("Chart 7 saved: ROC curve")

# Chart 8: Feature Importance
fig, ax = plt.subplots(figsize=(8, 6))
importance_df = pd.DataFrame({
    'feature': FEATURES,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=True)

bars = ax.barh(importance_df['feature'], importance_df['importance'],
               color='#378ADD')
ax.set_title('Feature Importance — What Drives Dropout?', fontsize=13)
ax.set_xlabel('Importance Score')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '8_feature_importance.png'), dpi=150)
plt.close()
print("Chart 8 saved: feature importance")

# ================================================
# Save Model
# ================================================
model_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\dropout_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

# Save encoder too
encoder_path = r'C:\Users\vaish\OneDrive\Documents\AiProject\label_encoder.pkl'
with open(encoder_path, 'wb') as f:
    pickle.dump(le, f)

print(f"\nModel saved: dropout_model.pkl")
print(f"Encoder saved: label_encoder.pkl")

# ================================================
#  Test Live Prediction
# ================================================
print("\n" + "=" * 50)
print("LIVE PREDICTION TEST")
print("=" * 50)

sample_student = pd.DataFrame([{
    'age': 22,
    'baseline_score': 45.0,
    'progress_pct': 30.0,
    'avg_duration': 25.0,
    'total_sessions': 3,
    'avg_score': 35.0,
    'failed_count': 2,
    'dropout_probability': 0.75,
    'learning_style_encoded': 1,
    'risk_level_encoded': 2
}])

prediction = model.predict(sample_student)[0]
probability = model.predict_proba(sample_student)[0][1]

print(f"\nStudent profile:")
print(f"  Age: 22, Progress: 30%, Avg Score: 35, Failed: 2 times")
print(f"\nPrediction: {'WILL DROP OUT' if prediction == 1 else 'WILL STAY'}")
print(f"Dropout probability: {probability * 100:.1f}%")
print("Dropout prediction model is trained and saved.")
