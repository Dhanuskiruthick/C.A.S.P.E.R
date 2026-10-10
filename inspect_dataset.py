
import pandas as pd
from pathlib import Path

folder = Path("data_test")
files = list(folder.glob("*.csv"))

if not files:
    raise FileNotFoundError("No CSV found inside data_test!")

csv_path = files[0]
df = pd.read_csv(csv_path)

print("Dataset:", csv_path.name)
print("Rows and columns:", df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nMissing values:", df.isnull().sum().sum())

print("\nAlarm label counts:")
if "Fire Alarm" in df.columns:
    print(df["Fire Alarm"].value_counts(dropna=False))
else:
    print("No 'Fire Alarm' column found.")

print("\nSample rows:")
print(df.head(5).to_string(index=False))
