#!/bin/bash

# Check if the required arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <script_file> <schedule> <job_description>"
    echo "Example: $0 /path/to/your_script.sh "* * * * *" \"Run script every minute\""
    exit 1
fi

script_file="$1"
schedule="$2"
job_description="$3"

# Validate the schedule
if ! [[ $schedule =~ ^[0-9*\/,-]+$ ]]; then
    echo "Invalid schedule format."
    exit 1
fi

# Create a unique identifier for the job
job_id=$(echo "$job_description" | tr ' ' '_')

# Define the cron job command
cron_command="$script_file"

# Add the job to the user's crontab
(crontab -l 2>/dev/null; echo "$schedule $cron_command # $job_description") | crontab -

echo "Cron job created:"
echo "Schedule: $schedule"
echo "Job Description: $job_description"
echo "Command: $cron_command"
