# pip install bs4 email-validator

import os
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
from email_validator import validate_email, EmailNotValidError

def extract_emails(file_path):
    emails = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', line)
                for email in email_matches:
                    emails.add(email.lower())
    except UnicodeDecodeError:
        print(f"Unable to decode file: {file_path}")
    return emails

def extract_emails_from_directory(directory):
    all_emails = set()
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            all_emails.update(extract_emails(file_path))
    return all_emails

def validate_email_wrapper(email):
    try:
        validate_email(email, check_deliverability=True)
        return email
    except EmailNotValidError as e:
        return e

def validate_emails(emails):
    with ThreadPoolExecutor() as executor:
        results = executor.map(validate_email_wrapper, emails)
    return results

def main():
    parser = argparse.ArgumentParser(description="Grab emails from all files in a directory")
    parser.add_argument("directory_path", help="Path to the directory containing files")
    args = parser.parse_args()

    directory = args.directory_path
    if not os.path.isdir(directory):
        print("Invalid directory path.")
        return

    all_emails = extract_emails_from_directory(directory)
    results = validate_emails(all_emails)
    
    output_file = 'emails.txt'
    with open(output_file, 'a') as f:
        for result in results:
            if isinstance(result, EmailNotValidError):
                print(f"Invalid email: {result}")
            else:
                f.write(result + '\n')

if __name__ == "__main__":
    main()
