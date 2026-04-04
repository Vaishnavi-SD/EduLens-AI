import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split # type: ignore
from sklearn.preprocessing import LabelEncoder # type: ignore
from sklearn.metrics import (accuracy_score, classification_report, # type: ignore
                             confusion_matrix, roc_auc_score, roc_curve)
from xgboost import XGBClassifier

try:
    from imblearn.over_sampling import SMOTE  # type: ignore
except ImportError:
    SMOTE = None

print("=" * 50)
print("EduLens AI — Dropout Prediction Model")
print("=" * 50)

df = pd.read_csv(r'C:\Users\vaish\OneDrive\Documents\AiProject\ml_dataset.csv')
print(f"\nDataset loaded: {df.shape[0]} students, {df.shape[1]} features")

le = LabelEncoder()
df['learning_style_encoded'] = le.fit_transform(df['learning_style'].fillna('unknown'))
risk_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
df['risk_level_encoded'] = df['risk_level'].map(risk_map).fillna(0)

FEATURES = [
    'age', 'baseline_score', 'progress_pct',
    'avg_duration', 'total_sessions', 'avg_score',
    'failed_count', 'dropout_probability',
    'learning_style_encoded', 'risk_level_encoded'
]
TARGET = 'dropout_label'

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

if SMOTE is not None:
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)
    print(f"\nAfter SMOTE balancing:")
    print(f"Training set: {len(X_train)} students (balanced)")
else:
    print("\nSMOTE skipped: imbalanced-learn is not installed.")
    print("Install it with: pip install imbalanced-learn")


print(f"Training set: {X_train.shape[0]} | Test set: {X_test.shape[0]}")

model = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    scale_pos_weight=3,
    eval_metric='logloss',
    random_state=42
)

print("\nTraining model...")
model.fit(X_train, y_train)
print("Model trained!")

y_pred = model.predict(X_test)
y_pred_prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_pred_prob)

print("\n" + "=" * 50)
print("MODEL PERFORMANCE")
print("=" * 50)
print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"ROC-AUC:   {roc_auc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred,
      target_names=['Not Dropout', 'Dropout']))

charts_dir = r'C:\Users\vaish\OneDrive\Documents\AiProject\charts'
os.makedirs(charts_dir, exist_ok=True)
sns.set_theme(style='whitegrid')

fig, ax = plt.subplots(figsize=(6, 5))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Not Dropout', 'Dropout'],
            yticklabels=['Not Dropout', 'Dropout'])
ax.set_title(f'Confusion Matrix (Accuracy: {accuracy*100:.1f}%)')
ax.set_ylabel('Actual')
ax.set_xlabel('Predicted')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '6_confusion_matrix.png'), dpi=150)
plt.close()

fpr, tpr, _ = roc_curve(y_test, y_pred_prob)
fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(fpr, tpr, color='#378ADD', lw=2,
        label=f'AUC = {roc_auc:.3f}')
ax.plot([0, 1], [0, 1], 'gray', linestyle='--')
ax.set_title('ROC Curve — Dropout Prediction')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '7_roc_curve.png'), dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(8, 6))
imp_df = pd.DataFrame({
    'feature': FEATURES,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=True)
ax.barh(imp_df['feature'], imp_df['importance'], color='#378ADD')
ax.set_title('Feature Importance — What Drives Dropout?')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '8_feature_importance.png'), dpi=150)
plt.close()
print("Charts saved!")

with open(r'C:\Users\vaish\OneDrive\Documents\AiProject\dropout_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open(r'C:\Users\vaish\OneDrive\Documents\AiProject\label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)
print("Model saved!")

sample = pd.DataFrame([{
    'age': 22, 'baseline_score': 45.0, 'progress_pct': 30.0,
    'avg_duration': 25.0, 'total_sessions': 3, 'avg_score': 35.0,
    'failed_count': 2, 'dropout_probability': 0.75,
    'learning_style_encoded': 1, 'risk_level_encoded': 2
}])
pred = model.predict(sample)[0]
prob = model.predict_proba(sample)[0][1]
print(f"\nLive Test — Prediction: {'WILL DROP OUT' if pred==1 else 'WILL STAY'}")
print(f"Dropout probability: {prob*100:.1f}%")
