# pip install bs4 email-validator

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from email_validator import validate_email, EmailNotValidError

def extract_emails(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        text_nodes = soup.find_all(string=True)
        emails = set()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for node in text_nodes:
            matches = re.findall(email_pattern, node)
            emails.update(matches)
    return emails

def validator(email, check_deliverability=False):
    try:
        if check_deliverability:
            validate_email(email, check_deliverability=True)
        else:
            validate_email(email)
        return email
    except EmailNotValidError as e:
        return e

def validate_emails(emails):
    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda email: (email, validator(email, check_deliverability=True)), emails)
    return results

def main(directory_path):
    all_emails = set()
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        emails = extract_emails(file_path)
        all_emails.update(emails)
    
    results = validate_emails(all_emails)
    for email, result in results:
        if isinstance(result, EmailNotValidError):
            print(f"Invalid email: {email}")
        else:
            with open('emails.txt', 'a') as f:
                f.write(email + '\n')
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Grab emails from all html files in a directory")
        print("Usage: python3 get_emails.py <directory_path>")
        sys.exit(1)
    main(sys.argv[1])
