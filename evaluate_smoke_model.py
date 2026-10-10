
import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
)

# Load saved model and dataset
bundle = joblib.load("models/smoke_classifier.joblib")
model = bundle["model"]
features = bundle["features"]

df = pd.read_csv("data_test/smoke_detection_iot.csv")
df = df.sort_values("UTC").reset_index(drop=True)

# Use the final 20% as a chronological evaluation segment
split_index = int(len(df) * 0.8)
test_df = df.iloc[split_index:].copy()

X_test = test_df[features]
y_test = test_df["Fire Alarm"].astype(int)

predictions = model.predict(X_test)

tn, fp, fn, tp = confusion_matrix(
    y_test, predictions, labels=[0, 1]
).ravel()

print("\nSMOKE MODEL EVALUATION")
print("----------------------")
print("Evaluation rows:", len(test_df))
print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    labels=[0, 1],
    target_names=["No alarm", "Fire alarm"],
    zero_division=0,
))

print("Confusion matrix [[TN, FP], [FN, TP]]:")
print([[tn, fp], [fn, tp]])

print("\nFALSE ALARM ANALYSIS")
print("False positives:", fp)
print("No-alarm samples incorrectly flagged:", fp)
print("Missed alarm-positive samples:", fn)
print("Correctly detected alarm-positive samples:", tp)

if tn + fp:
    print(f"False-positive rate: {fp / (tn + fp):.2%}")

if tp + fn:
    print(f"Miss rate: {fn / (tp + fn):.2%}")
