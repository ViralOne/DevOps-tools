import requests
import sys
import time
from urllib.parse import urlparse
from termcolor import colored

# List of websites to check
websites = [
    "https://google.com",
    "https://examplase.com"
]

def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

def check_website(website):
    try:
        response = requests.get(website)
        domain = get_domain(website)
        if response.status_code == 200:
            print(f"{domain} is accessible and returned a status code of 200 OK.")
        else:
            error_message = f"{domain} returned a status code of {response.status_code}. There may be an issue."
            colored_error = colored(error_message, "red", attrs=["reverse", "blink"])
            print(colored_error)
    except requests.exceptions.RequestException as e:
        domain = get_domain(website)
        print(f"An error occurred while accessing {domain}: {e}")

def main():
    while True:
        for website in websites:
            check_website(website)
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Execution stopped by user.")
        sys.exit(0)
