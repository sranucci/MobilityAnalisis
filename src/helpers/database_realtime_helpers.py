from helpers.database_helpers import fetch_gtfs_realtime_data
import time
import pandas as pd


def extract_vehicle_positions(feed):
    vehicle_positions = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            vehicle_positions.append({
                "id": entity.id,
                "trip_id": vehicle.trip.trip_id,
                "schedule_relationship": vehicle.trip.schedule_relationship,
                "latitude": vehicle.position.latitude,
                "longitude": vehicle.position.longitude,
                "bearing": vehicle.position.bearing,
                "speed": vehicle.position.speed * 3.6, # Speed in km/h
                "current_status": vehicle.current_status,
                "timestamp": vehicle.timestamp,
                "stop_id": vehicle.stop_id,
                "vehicle_id": vehicle.vehicle.id,
                "vehicle_label": vehicle.vehicle.label,
                "vehicle_license_plate": vehicle.vehicle.license_plate
            })
    return vehicle_positions

# Function that collects a sequence of timestamped positions from a real-time feed
def collect_vehicle_positions(duration_minutes, interval_seconds):
    collected_data = []
    end_time = time.time() + duration_minutes * 60 # Convert minutes to seconds
    while time.time() < end_time:
        # Fetch the GTFS Realtime data
        feed = fetch_gtfs_realtime_data()
        # If feed is fetched, extract vehicle positions
        if feed:
            vehicle_positions = extract_vehicle_positions(feed)
            if vehicle_positions:
                collected_data.extend(vehicle_positions) # Add the new data to the list
        else:
            print("Failed to fetch the GTFS Realtime feed.")
        # Wait for the specifed interval before making the next request
        time.sleep(interval_seconds)
    # Convert the collected data into a DataFrame
    df = pd.DataFrame(collected_data)
    return df