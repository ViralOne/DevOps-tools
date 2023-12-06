import re
from urllib.parse import urlparse

def extract_urls_from_text(text_data):
    url_pattern = r'https?://[^\s"]+'
    return re.findall(url_pattern, text_data)

def clean_urls(urls):
    unique_domains = set()
    for url in urls:
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        unique_domains.add(domain)
    return list(unique_domains)

def save_urls_to_file(urls, output_file):
    with open(output_file, 'w') as file:
        file.write('\n'.join(urls))

def main():
    input_file = 'input.txt'
    output_file = 'domains.txt'

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            file_content = file.read()

            urls = extract_urls_from_text(file_content)
            cleaned_domains = clean_urls(urls)

            save_urls_to_file(cleaned_domains, output_file)

            print(f"Extracted {len(cleaned_domains)} URLs from the file. Saved to '{output_file}'.")
    except FileNotFoundError:
        print(f"File '{input_file}' not found.")

if __name__ == "__main__":
    main()
