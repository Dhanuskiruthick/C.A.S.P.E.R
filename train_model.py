
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

# 1. Generate sample sensor readings
# These are simulated values for learning purposes.
rng = np.random.default_rng(42)

normal_data = pd.DataFrame({
    "temperature_c": rng.normal(30, 2, 1000),
    "current_a": rng.normal(4, 0.5, 1000)
})

# 2. Create the anomaly detection model
model = IsolationForest(
    contamination=0.03,
    random_state=42
)

# 3. Train using normal-operation data
model.fit(normal_data)

# 4. Save the trained model
model_bundle = {
    "model": model,
    "features": ["temperature_c", "current_a"]
}

joblib.dump(model_bundle, "models/campus_anomaly_model.joblib")

print("Model trained successfully!")
print("Model saved in the models folder.")