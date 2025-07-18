#!/bin/bash

# Script to unzip tec_gtfs.zip in the gtfs folder, with option to skip unzipping

SKIP_UNZIP=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-unzip)
            SKIP_UNZIP=1
            shift
            ;;
    esac
done

# Navigate to the gtfs directory
cd gtfs

# Check if the zip file exists
if [ ! -f "tec_gtfs.zip" ]; then
    echo "Error: tec_gtfs.zip not found in the gtfs directory"
    exit 1
fi

if [ $SKIP_UNZIP -eq 0 ]; then
    # Unzip the file in the same directory
    echo "Unzipping tec_gtfs.zip..."
    unzip -o tec_gtfs.zip

    # Check if unzip was successful
    if [ $? -eq 0 ]; then
        echo "Successfully unzipped tec_gtfs.zip"
        echo "Contents of gtfs directory:"
        ls -la
    else
        echo "Error: Failed to unzip tec_gtfs.zip"
        exit 1
    fi
else
    echo "Skipping unzip as per --skip-unzip flag."
fi



npm exec -- gtfs-to-sql --require-dependencies -- *.txt | psql -h localhost -U postgres -d mobility -b