import os
import json
import psycopg2
from dotenv import load_dotenv
from gtfs.ex1 import doExcersise1
from helpers.database_helpers import get_db_conn
from gtfs.ex2 import doExcersise2
from gtfs.ex3 import doExercise3
from gtfs.ex4 import doExercise4
from gtfsrt.ex1dots import doExerciseRealtime1
from gtfsrt.ex1Trajectory import doExerciseRealtime1Trajectory
from gtfsrt.ex1TrajectoryAll import doExcersise1TrajectoryAllRealtime
from gtfsrt.ex2AverageSpeeds import doExercise2RealtimeAverageSpeeds
from gtfsrt.ex3DelayPerStopAverage import doExercise3DelayPerStopRealtime
from gtfsrt.ex4DelayPerSegment import doExercise4SegmentsDelayMap





def main():
    load_dotenv()

  
    conn = get_db_conn()
    cur = conn.cursor()

    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)


    with open("runconfig.json", "r") as config_file:
        config = json.load(config_file)

    if config.get("gtfs", {}).get("ex1", {}):
        doExcersise1(cur, results_dir, config.get("gtfs", {}).get("ex1", {}))
    if config.get("gtfs", {}).get("ex2", {}).get("display", False):
        doExcersise2(cur, results_dir, config.get("gtfs", {}).get("ex2", {}))
    if config.get("gtfs", {}).get("ex3", {}).get("display", False):
        doExercise3(cur, results_dir, config.get("gtfs", {}).get("ex3", {}))
    if config.get("gtfs", {}).get("ex4", {}).get("display", False):
        doExercise4(cur, results_dir)


    display_dots = config.get("gtfsRealtime", {}).get("ex1", {}).get("displayDots", {}).get("display", False)
    display_trajectory = config.get("gtfsRealtime", {}).get("ex1", {}).get("displayTrajectory", {}).get("display", False)
    if display_dots and display_trajectory:
        raise Exception("Cannot display both Dots and Trajectory at the same time. Please enable only one in the config.")

    if display_dots:
        app = doExerciseRealtime1(cur)
        app.run(debug=True, host="0.0.0.0", port=8050)
    elif display_trajectory:
        app = doExerciseRealtime1Trajectory(cur)
        app.run(debug=True, host="0.0.0.0", port=8051)

    if config.get("gtfsRealtime", {}).get("ex1", {}).get("displayAllTrajectories", {}).get("display", False):
        doExcersise1TrajectoryAllRealtime(cur, results_dir)

    if config.get("gtfsRealtime", {}).get("ex2", {}).get("displayRealTimeAverageSpeeds", False):
        doExercise2RealtimeAverageSpeeds(cur, results_dir)
    if config.get("gtfsRealtime", {}).get("ex3", {}).get("displayStopsDelay", False):
        doExercise3DelayPerStopRealtime(cur, results_dir)
    if config.get("gtfsRealtime", {}).get("ex3", {}).get("displaySegmentsDelay", False):
        doExercise4SegmentsDelayMap(cur, results_dir)

    # Clean up
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
