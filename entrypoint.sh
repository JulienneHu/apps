#!/bin/bash


# Ensure the script to run is provided
if [ -z "$SCRIPT_NAME" ]; then
    echo "No script specified in SCRIPT_NAME. Exiting."
    exit 1
fi

# Run the specified script
echo "Running script: $SCRIPT_NAME"
conda run -n myenv python /app/$SCRIPT_NAME
