import os
import json
import psycopg2
from dotenv import load_dotenv
from gtfs.ex1 import doExcersise1
from helpers.database_helpers import get_db_conn
from gtfs.ex2 import doExcersise2

def main():
    # Load environment variables from .env file
    load_dotenv()

  
    # Establish DB connection using environment variables
    conn = get_db_conn()
    cur = conn.cursor()

    # Create 'results' folder if it doesn't exist
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)


    # Load the configuration from runconfig.json
    with open("runconfig.json", "r") as config_file:
        config = json.load(config_file)

    # Yes, this is checking if the value of "display" is True (a boolean).
    if config.get("gtfs", {}).get("ex1", {}).get("display", False):
        result_map = doExcersise1(cur, results_dir,config.get("gtfs", {}).get("ex1", {}))
        result_map.save(os.path.join(results_dir, "exercise1_map.html"))
        print(f"✅ Map saved to '{os.path.join(results_dir, 'exercise1_map.html')}'. Open this file in your browser.")
    elif config.get("gtfs", {}).get("ex2", {}).get("display", False):
        doExcersise2(cur,results_dir,config.get("gtfs", {}).get("ex2", {}))

    # Clean up
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
