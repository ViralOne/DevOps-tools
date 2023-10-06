import sys
import signal

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
