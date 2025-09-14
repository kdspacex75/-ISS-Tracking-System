import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV log
df = pd.read_csv("iss_log.csv", parse_dates=["timestamp"])

# Convert dist to numeric
df["dist_km"] = pd.to_numeric(df["dist_km"], errors="coerce")

# Plot
plt.figure(figsize=(10,5))
plt.plot(df["timestamp"], df["dist_km"], marker="o", linestyle="-")
plt.title("ISS Distance from Home Location")
plt.xlabel("Time")
plt.ylabel("Distance (km)")
plt.grid(True)

# Mark when ISS was near
near = df[df["state"]=="S"]
if not near.empty:
    plt.scatter(near["timestamp"], near["dist_km"], color="red", label="NEAR ISS", zorder=5)
    plt.legend()

plt.tight_layout()
plt.show()
