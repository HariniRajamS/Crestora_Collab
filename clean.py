import pandas as pd
from pathlib import Path

path = Path("market_rounds.csv")

df = pd.read_csv(path)
print("Before cleaning:", df.shape)

# Strip column names and data
df.columns = [c.strip() for c in df.columns]
df["company"] = df["company"].astype(str).str.strip()
df["round"] = df["round"].astype(str).str.extract(r"(\d+)")[0].astype(int)
df["price"] = df["price"].astype(float)
df = df.sort_values(["round", "company"]).reset_index(drop=True)

# Check for missing combos
companies = df["company"].unique()
rounds = sorted(df["round"].unique())
for comp in companies:
    for rnd in rounds:
        if df[(df["round"] == rnd) & (df["company"] == comp)].empty:
            print(f"❌ Missing {comp} round {rnd}")

# Save cleaned version
df.to_csv(path, index=False)
print("✅ Clean CSV saved:", path)
