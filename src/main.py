import os
import json
import psycopg2
from dotenv import load_dotenv
from gtfs.ex1 import doExcersise1
from helpers.database_helpers import get_db_conn
from gtfs.ex2 import doExcersise2
from gtfs.ex3 import doExercise3
from gtfs.ex4 import doExercise4


def main():
    load_dotenv()

  
    conn = get_db_conn()
    cur = conn.cursor()

    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)


    with open("runconfig.json", "r") as config_file:
        config = json.load(config_file)

    if config.get("gtfs", {}).get("ex1", {}):
        doExcersise1(cur, results_dir,config.get("gtfs", {}).get("ex1", {}))
    if config.get("gtfs", {}).get("ex2", {}).get("display", False):
        doExcersise2(cur,results_dir,config.get("gtfs", {}).get("ex2", {}))
    if config.get("gtfs", {}).get("ex3", {}).get("display", False):
        doExercise3(cur,results_dir,config.get("gtfs", {}).get("ex3", {}))
    if config.get("gtfs", {}).get("ex4", {}).get("display", False):
        doExercise4(cur,results_dir)

    # Clean up
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
