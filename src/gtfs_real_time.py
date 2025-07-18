import os
from dotenv import load_dotenv
import requests

from google.transit import gtfs_realtime_pb2

# Load environment variables from .env file
load_dotenv()

url = "https://api.mobilitytwin.brussels/tec/gtfs-realtime"

api_key = os.environ.get("API_KEY")
if not api_key:
    raise EnvironmentError("API_KEY environment variable not set.")

data = requests.get(url, headers={
        'Authorization': f'Bearer {api_key}'
}).content

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(data)
for entity in feed.entity:
    print(entity)  # You can start by just printing it to inspect the structure
