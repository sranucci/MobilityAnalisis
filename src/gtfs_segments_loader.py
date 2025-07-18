import os
from dotenv import load_dotenv

import gtfs_functions as gtfs

from helpers.database_helpers import geodataframe_to_postgis

def main():
    load_dotenv()
    # Read config from environment, with fallbacks
    gtfs_zip = str(os.getenv(
        "GTFS_FILE_PATH",
    ))
    start_date = os.getenv("GTFS_START_DATE")
    end_date   = os.getenv("GTFS_END_DATE")

    # Fetch and persist
    feed = gtfs.Feed(gtfs_zip, start_date=start_date, end_date=end_date)
    segmentsdf = feed.segments
    geodataframe_to_postgis(segmentsdf)
    print(f"Saving to DB")
    

if __name__ == "__main__":
    main()
