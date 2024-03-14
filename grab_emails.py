import os
import re
import sys
from bs4 import BeautifulSoup

def extract_emails_from_html(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        text_nodes = soup.find_all(string=True)
        emails = set()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for node in text_nodes:
            matches = re.findall(email_pattern, node)
            emails.update(matches)
    return emails

def main(directory_path):
    all_emails = set()
    for file_name in os.listdir(directory_path):
        if file_name.endswith('.html'):
            file_path = os.path.join(directory_path, file_name)
            emails = extract_emails_from_html(file_path)
            all_emails.update(emails)
    
    print("Unique Email Addresses:")
    for email in all_emails:
        print(email)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Grab emails from all html files in a directory")
        print("Usage: python3 get_emails.py <directory_path>")
        sys.exit(1)
    main(sys.argv[1])
