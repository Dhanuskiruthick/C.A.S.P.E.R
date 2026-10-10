
import joblib
import pandas as pd

MODEL_PATH = "models/smoke_classifier.joblib"

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
features = bundle["features"]

# DEMO ONLY: replace these with actual readings
# in the same units and feature order as the training dataset.
sample = {
    "Temperature[C]": 25.0,
    "Humidity[%]": 50.0,
    "TVOC[ppb]": 100.0,
    "eCO2[ppm]": 450.0,
    "Raw H2": 13000.0,
    "Raw Ethanol": 19000.0,
    "Pressure[hPa]": 939.0,
    "PM1.0": 5.0,
    "PM2.5": 8.0,
    "NC0.5": 30.0,
    "NC1.0": 10.0,
    "NC2.5": 1.0,
}

X = pd.DataFrame([sample], columns=features)
prediction = int(model.predict(X)[0])

if prediction == 1:
    print("MODEL OUTPUT: FIRE ALARM")
else:
    print("MODEL OUTPUT: NO ALARM")

print("Predicted class:", prediction)
