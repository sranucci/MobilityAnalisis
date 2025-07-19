import os
import pyarrow.parquet as pq
import pyarrow as pa
import json
import pandas as pd

from helpers.database_realtime_helpers import collect_vehicle_positions

def save_to_parquet(df, fileName):
  if not df.empty:
    table = pa.Table.from_pandas(df)
    pq.write_table(table, fileName)
    print(f"Data successfully saved to {fileName}")
  else:
    print("No data to save.")

# Create gtfsrt directory if it doesn't exist
gtfsrt_dir = os.path.join(os.getcwd(), "gtfsrt")
os.makedirs(gtfsrt_dir, exist_ok=True)

# Define file paths
parquet_file = os.path.join(gtfsrt_dir, "valonia_vehicle_positions.parquet")
csv_file = os.path.join(gtfsrt_dir, "valonia_vehicle_positions.csv")

# Load the configuration from runconfig.json
with open("runconfig.json", "r") as config_file:
    config = json.load(config_file)

fetchConfig = config.get("gtfsRealtime", {}).get("fetchData", {})
durationMinutes = fetchConfig.get("durationMinutes")
intervalSeconds = fetchConfig.get("intervalSeconds")
print(f"Starting data collection for {durationMinutes} minutes, querying every {intervalSeconds} seconds...")
vehiclePositionsDf = collect_vehicle_positions(durationMinutes, intervalSeconds)
# Save the data to a Parquet file
save_to_parquet(vehiclePositionsDf, parquet_file)

# Convert the Parquet file to CSV in the same directory
if not vehiclePositionsDf.empty:
    # Load Parquet file into a DataFrame (could also use vehiclePositionsDf directly)
    df = pd.read_parquet(parquet_file)
    df.to_csv(csv_file, index=False)
    print(f"CSV saved to: {csv_file}")
else:
    print("No data to convert to CSV.")
