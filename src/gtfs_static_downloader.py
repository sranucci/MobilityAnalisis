import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()


url = "https://api.mobilitytwin.brussels/tec/gtfs"


api_key = os.environ.get("API_KEY")
if not api_key:
    raise EnvironmentError("API_KEY environment variable not set.")

# Make the request
response = requests.get(url, headers={
    'Authorization': f'bearer {api_key}'
})
data = response.content

# Create gtfs directory if it doesn't exist
gtfs_dir = os.path.join(os.getcwd(), "gtfs")
os.makedirs(gtfs_dir, exist_ok=True)

# Define file path
file_path = os.path.join(gtfs_dir, "tec_gtfs.zip")

# Write file
with open(file_path, 'wb') as f:
    f.write(data)

