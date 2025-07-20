#!/bin/bash

# Script to unzip google_transit.zip in the gtfs folder and load GTFS data into PostgreSQL

# Check for required DB arguments
if [ "$#" -lt 4 ]; then
    echo "Usage: $0 <host> <user> <database> <password>"
    exit 1
fi

PGHOST=$1
PGUSER=$2
PGDATABASE=$3
PGPASSWORD=$4

# Navigate to the gtfs directory
cd gtfs || { echo "Error: gtfs directory not found"; exit 1; }

# Check if the zip file exists
if [ ! -f "google_transit.zip" ]; then
    echo "Error: google_transit.zip not found in the gtfs directory"
    exit 1
fi

# Unzip the file in the same directory
echo "Unzipping google_transit.zip..."
unzip -o google_transit.zip

if [ $? -eq 0 ]; then
    echo "Success unzipping"
    echo "Contents of gtfs directory:"
    ls -la
else
    echo "Error: Failed to unzip"
    exit 1
fi

for file in *.txt; do
  sed -i 's/ *, */,/g' "$file"  # remove spaces around commas
done


# Export password and run gtfs-to-sql + psql
export PGPASSWORD
npm exec -- gtfs-to-sql --require-dependencies -- *.txt | psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -b
unset PGPASSWORD
