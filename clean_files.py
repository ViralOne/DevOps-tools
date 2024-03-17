# pip install bs4
# If word exists in file delete the file

import os
import sys
from bs4 import BeautifulSoup

def find_words(file_path, words):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        for word in words:
            if soup.find(string=lambda text: text and word in text):
                return True
    return False

def delete_files_with_words(directory, words):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.html'):
                file_path = os.path.join(root, filename)
                if find_words(file_path, words):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <root_directory_path> <words_file_path>")
        sys.exit(1)

    root_directory = sys.argv[1]
    words_file_path = sys.argv[2]

    if not os.path.isdir(root_directory):
        print("Error: Root directory does not exist.")
        sys.exit(1)

    if not os.path.isfile(words_file_path):
        print("Error: Words file does not exist.")
        sys.exit(1)

    with open(words_file_path, 'r') as f:
        words_to_search = [line.strip() for line in f.readlines() if line.strip()]

    delete_files_with_words(root_directory, words_to_search)
