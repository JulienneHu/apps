#!/bin/bash

# Check if the database file exists
if [ ! -f /app/trades.db ]; then
    echo "Database not found. Initializing new database at /app/trades.db..."
    # Your database initialization commands here, e.g., creating tables
else
    echo "Database found at /app/trades.db."
fi

# Ensure the script to run is provided
if [ -z "$SCRIPT_NAME" ]; then
    echo "No script specified in SCRIPT_NAME. Exiting."
    exit 1
fi

# Run the specified script
echo "Running script: $SCRIPT_NAME"
conda run -n myenv python /app/$SCRIPT_NAME
