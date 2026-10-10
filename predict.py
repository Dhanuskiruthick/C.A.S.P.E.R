
import joblib
import pandas as pd

# Load the trained anomaly detection model
bundle = joblib.load("models/campus_anomaly_model.joblib")
model = bundle["model"]
features = bundle["features"]

# Example sensor reading
reading = pd.DataFrame(
    [{"temperature_c": 48.0, "current_a": 8.7}],
    columns=features
)

# Predict whether the reading is unusual
prediction = model.predict(reading)[0]

print("Sensor reading:")
print(reading.to_string(index=False))

if prediction == -1:
    print("WARNING: Unusual sensor pattern detected!")
else:
    print("NORMAL: Sensor pattern looks typical.")
