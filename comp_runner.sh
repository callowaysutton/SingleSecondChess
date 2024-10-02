#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the script 100 times in parallel, logging output to numbered files
for i in $(seq 1 100); do
    # Format the log file name (e.g., game_001.log, game_002.log, ...)
    log_file=$(printf "logs/game_%03d.log" $i)

    # Run the script and redirect output to the log file
    ./airgap_runner.sh > "$log_file" &

    # Optional: Add a small sleep if you don't want all processes to start at exactly the same time
    sleep 10
done

# Wait for all background processes to complete
wait

echo "All processes completed."
