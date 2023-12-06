import requests
import concurrent.futures
import os
from datetime import datetime
import sys

# Constants
NUM_THREADS = 10
TIMEOUT_CONNECT = 10.0
TIMEOUT_READ = 10.0
GOOD_STATUS = {200, 403, 503}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

# Check login with headers to not be detected as bot
def check_domain(domain):
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = requests.get(domain, headers=headers, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ), allow_redirects=True)
        return domain, response.status_code
    except requests.Timeout as e:
        return domain, f"Timeout occurred: {str(e)}"
    except requests.HTTPError as e:
        return domain, f"HTTP error occurred: {str(e)}"
    except requests.RequestException as e:
        return domain, f"Other error occurred: {str(e)}"

def read_domains_from_file(domain_file):
    with open(domain_file, 'r') as file:
        return [domain.strip() for domain in file.readlines()]

def check_domains(domain_file):
    domains = read_domains_from_file(domain_file)
    total_domains = len(domains)
    domains_checked = 0
    results = {}
    progress_interval = max(total_domains // 10, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = {executor.submit(check_domain, domain): domain for domain in domains}
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results[result[0]] = result[1]
            except Exception as e:
                results[futures[future]] = str(e)

            domains_checked += 1
            if domains_checked % progress_interval == 0 or domains_checked == total_domains:
                progress = domains_checked / total_domains * 100
                sys.stdout.write(f"\rDomains Checked: {domains_checked}/{total_domains} [{progress:.2f}%]")
                sys.stdout.flush()
    return results

def filter_domains(results):
    working_domains = {}
    not_working_domains = {}
    for domain, status_code in results.items():
        if isinstance(status_code, int) and status_code in GOOD_STATUS:
            working_domains[domain] = status_code
        else:
            not_working_domains[domain] = status_code
    return working_domains, not_working_domains

def save_results_to_file(results):
    working_domains, not_working_domains = results
    output_folder = 'result'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_good_domains = os.path.join(output_folder, f'output_good_{current_datetime}.txt')
    output_bad_domains = os.path.join(output_folder, f'output_bad_{current_datetime}.txt')

    with open(output_good_domains, 'w') as file:
        file.write("\n".join(working_domains.keys()))
    with open(output_bad_domains, 'w') as file:
        for domain, status_code in not_working_domains.items():
            file.write(f"{domain}\n")
    print(f"\nDomain check results saved in the '{output_folder}' folder.")

def main():
    domain_file = 'domains.txt'

    try:
        filtered_results = filter_domains(check_domains(domain_file))
        save_results_to_file(filtered_results)
    except FileNotFoundError:
        print(f"File '{domain_file}' not found.")

if __name__ == "__main__":
    main()
