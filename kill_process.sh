#!/bin/bash
app_name="gradle"

# Check if the process is running
if pgrep -x "$app_name" > /dev/null; then
    # Get the process ID (PID)
    app_pid=$(pgrep -x "$app_name")
    
    # Kill the process
    kill "$app_pid"
    
    echo "Process $app_name (PID $app_pid) has been terminated."
else
    echo "Process $app_name is not running."
fi
