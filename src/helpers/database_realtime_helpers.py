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
    """
    Extrae de cada trip_update:
     - trip info (trip_id, start_time, start_date, route_id)
     - por cada stop_time_update: stop_sequence, stop_id, arrival.delay, departure.delay
     - delay global (tu.delay)
     - vehicle.id si existe dentro de trip_update
    """
    records = []
    length = len(feed1.entity)
    for entity in feed1.entity:
            vehicle = entity.vehicle
            if vehicle.position.speed <= 0 or vehicle.position.latitude == 0 or vehicle.position.longitude == 0:
                continue
            tu = entity.trip_update
            base = {
                "entity_id": entity.id,
                "trip_id": tu.trip.trip_id,
                "start_time": tu.trip.start_time,
                "start_date": tu.trip.start_date,
                "route_id": tu.trip.route_id,
                "overall_delay": tu.delay if tu.HasField("delay") else None,
                "vehicle_id": tu.vehicle.id if tu.HasField("vehicle") else None,
                "bearing" : vehicle.position.bearing,
                "latitude": vehicle.position.latitude,
                "longitude": vehicle.position.longitude,
                "speed": vehicle.position.speed,
                "timestamp": vehicle.position.timestamp
            }
            # registros por parada
            for stu in tu.stop_time_update:
                records.append({
                    **base,
                    "stop_sequence": stu.stop_sequence,
                    "stop_id": stu.stop_id,
                    "arrival_delay": stu.arrival.delay if stu.arrival else None,
                    "departure_delay": stu.departure.delay if stu.departure else None,
                    "schedule_relationship": stu.schedule_relationship
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