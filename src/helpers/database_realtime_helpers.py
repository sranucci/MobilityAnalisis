import os
from dotenv import load_dotenv
import requests
import time
import pandas as pd
from google.transit import gtfs_realtime_pb2
from datetime import datetime, timedelta


def fetch_feed(url) -> gtfs_realtime_pb2.FeedMessage:
    load_dotenv()
    resp = requests.get(
        url,
    )
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def extract_trip_updates(feed1: gtfs_realtime_pb2.FeedMessage) -> list[dict]:
    records = []
    for entity in feed1.entity:
            vehicle = entity.vehicle
            if vehicle.position.speed <= 0 or vehicle.position.latitude == 0 or vehicle.position.longitude == 0:
                continue
            records.append({
                "entity_id": entity.id,
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
    return records

# Function that collects a sequence of timestamped positions from a real-time feed
def collect_vehicle_positions(duration_minutes, interval_seconds):
    collected_data = []
    end_time = time.time() + duration_minutes * 60 # Convert minutes to seconds
    while time.time() < end_time:
        # Fetch the GTFS Realtime data
        feed = fetch_feed("https://glphprdtmgtfs.glphtrpcloud.com/tmgtfsrealtimewebservice/vehicle/vehiclepositions.pb")
        # If feed is fetched, extract vehicle positions
        if feed:
            vehicle_positions = extract_trip_updates(feed)
            if vehicle_positions:
                collected_data.extend(vehicle_positions) # Add the new data to the list
        else:
            print("Failed to fetch the GTFS Realtime feed.")
        # Wait for the specifed interval before making the next request
        print("Collection success")
        time.sleep(interval_seconds)
    # Convert the collected data into a DataFrame
    df = pd.DataFrame(collected_data)
    return df