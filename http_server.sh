#!/bin/bash

SERVER="python3 -m http.server 3000"
PID=$(lsof -t -i:3000)

start_server() {
    if [ -z "$PID" ]
    then
        echo "Starting server..."
        $SERVER &>/dev/null &
        echo "Server started on port 3000."
    else
        echo "Server is already running with PID: $PID"
    fi
}

stop_server() {
    if [ -z "$PID" ]
    then
        echo "Server is not running."
    else
        echo "Stopping server with PID: $PID..."
        kill -9 $PID
        echo "Server stopped."
    fi
}

status_check() {
    if [ -z "$PID" ]
    then
        echo "Server is not running."
    else
        echo "Server is running with PID: $PID"
    fi
}

if [ $# -eq 0 ]
then
    echo "No arguments provided. Please specify start, stop or status as an argument."
    exit 1
fi

case "$1" in
start)
    start_server
    ;;
stop)
    stop_server
    ;;
status)
    status_check
    ;;
*)
    echo "Invalid option. Please specify start, stop or status as an argument."
    exit 1
    ;;
esac
