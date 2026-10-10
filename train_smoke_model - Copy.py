
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    recall_score,
)
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "smoke_detection_iot.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "smoke_classifier.joblib"

# Load dataset
df = pd.read_csv(DATA_PATH)

# Remove rows without a target label
df = df.dropna(subset=["Fire Alarm"])

# Remove metadata and target from model inputs.
# UTC is used only to order the observations.
excluded = ["Unnamed: 0", "UTC", "CNT", "Fire Alarm"]
features = [col for col in df.columns if col not in excluded]

# Sort by time to reduce leakage from nearby readings
if "UTC" in df.columns:
    df = df.sort_values("UTC").reset_index(drop=True)

# Convert selected features to numeric values
X = df[features].apply(pd.to_numeric, errors="coerce")
y = pd.to_numeric(df["Fire Alarm"], errors="coerce")

# Remove invalid labels
valid = y.isin([0, 1])
X = X.loc[valid].reset_index(drop=True)
y = y.loc[valid].astype(int).reset_index(drop=True)

# Chronological split: first 80% for training,
# final 20% for testing
split = int(len(df.loc[valid]) * 0.8)

X_train = X.iloc[:split]
X_test = X.iloc[split:]
y_train = y.iloc[:split]
y_test = y.iloc[split:]

# Build model pipeline
model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ))
])

# Train
model.fit(X_train, y_train)

# Evaluate on the later observations
predictions = model.predict(X_test)

print("\nMODEL EVALUATION")
print("----------------")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Features:", features)
print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
print("Fire-alarm recall:",
      round(recall_score(y_test, predictions, pos_label=1), 4))

print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    labels=[0, 1],
    target_names=["No alarm", "Fire alarm"],
    zero_division=0
))

print("Confusion matrix:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))

# Save model and its expected input features
MODEL_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump({
    "model": model,
    "features": features
}, MODEL_PATH)

print("\nModel trained successfully!")
print("Saved to:", MODEL_PATH)
