import requests
import sys, signal, time
from urllib.parse import urlparse
from termcolor import colored

# Handle Ctrl+C
def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

# List of websites to check
websites = [
    "https://google.com",
    "https://example.com"
]

def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def check_websites(websites):
    for website in websites:
        try:
            response = requests.get(website)
            domain = get_domain(website)
            if response.status_code == 200:
                print(f"{domain} is accessible and returned a status code of 200 OK.")
            else:
                error = colored(f"{domain} returned a status code of {response.status_code}. There may be an issue.", "red", attrs=["reverse", "blink"])
                print(error)
        except requests.exceptions.RequestException as e:
            domain = get_domain(website)
            print(f"An error occurred while accessing {domain}: {e}")

while True:
    check_websites(websites)
    time.sleep(10)
