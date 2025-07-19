import os
import pyarrow.parquet as pq
import pyarrow as pa
import json

from helpers.database_realtime_helpers import collect_vehicle_positions

def save_to_parquet(df, fileName):
  if not df.empty:
    table = pa.Table.from_pandas(df)
    pq.write_table(table, fileName)
    print(f"Data successfully saved to {fileName}")
  else:
    print("No data to save.")



# Create gtfs directory if it doesn't exist
gtfsrt_dir = os.path.join(os.getcwd(), "gtfsrt")
os.makedirs(gtfsrt_dir, exist_ok=True)

# Define file path
file_path = os.path.join(gtfsrt_dir, "valonia_vehicle_positions.parquet")
 # Load the configuration from runconfig.json
with open("runconfig.json", "r") as config_file:
    config = json.load(config_file)

    fetchConfig = config.get("gtfsRealtime", {}).get("fetchData", {})
    durationMinutes = fetchConfig.get("durationMinutes")
    intervalSeconds = fetchConfig.get("intervalSeconds")
    print(f"Starting data collection for {durationMinutes} minutes, querying every {intervalSeconds} seconds...")
    vehiclePositionsDf = collect_vehicle_positions(durationMinutes, intervalSeconds)
    # Save the data to a Parquet fle
    save_to_parquet(vehiclePositionsDf, file_path)


