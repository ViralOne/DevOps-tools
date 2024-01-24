import argparse
import random
import socket
import subprocess
import platform
import logging
import sys

# Constants
HOSTS_FILE_PATH_WINDOWS = r'C:\Windows\System32\drivers\etc\hosts'
HOSTS_FILE_PATH_MAC = '/etc/hosts'
NAMESERVERS_FILE_PATH = 'ns.txt'

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_nameserver(ns_list):
    return random.choice(ns_list)

def get_nameserver_ip(nameserver):
    return socket.gethostbyname(nameserver)

def update_hosts_file(domain, ip_address):
    hosts_file_path = get_hosts_file_path()
    with open(hosts_file_path, 'a+') as hosts_file:
        content = hosts_file.read()
        if f"{ip_address}   {domain}" not in content:
            hosts_file.write(f"\n{ip_address}   {domain}\n")

def remove_entries_from_hosts_file(domains):
    hosts_file_path = get_hosts_file_path()
    with open(hosts_file_path, 'r') as hosts_file:
        lines = hosts_file.readlines()
    with open(hosts_file_path, 'w') as hosts_file:
        for line in lines:
            if not any(domain in line for domain in domains):
                hosts_file.write(line)
        logger.info("Removed entries from hosts file")

def flush_dns_cache():
    if platform.system().lower() == 'windows':
        subprocess.run(['ipconfig', '/flushdns'], check=True)
    elif platform.system().lower() == 'darwin':
        subprocess.run(['dscacheutil', '-flushcache'], check=True)
    else:
        subprocess.run(['sudo', 'service', 'networking', 'restart'], check=True)

def get_hosts_file_path():
    system = platform.system().lower()
    if system == 'windows':
        return r'C:\Windows\System32\drivers\etc\hosts'
    elif system == 'darwin':
        return '/etc/hosts'
    else:
        return '/etc/hosts'

def load_domains_from_file(file):
    with open(file, 'r') as domains:
        return domains.read().splitlines()

def load_nameservers_from_file(file_path):
    try:
        with open(file_path, 'r') as ns_file:
            return ns_file.read().splitlines()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

def test_domains(domain_list, nameserver_list):
    for domain in domain_list:
        selected_nameserver = get_nameserver(nameserver_list)
        nameserver_ip = get_nameserver_ip(selected_nameserver)
        update_hosts_file(domain, nameserver_ip)
        print(f"Added {domain} using nameserver: {selected_nameserver} with IP: {nameserver_ip}")
    flush_dns_cache()

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description='Test domains and optionally remove entries from the hosts file.')
    parser.add_argument('-l', '--load', action='store_true', help='Add new entries to the hosts file')
    parser.add_argument('-r', '--remove', action='store_true', help='Remove entries from the hosts file')
    parser.add_argument('-f', '--file', default='domain.txt', help='Specify the configuration file (default: domain.txt)')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    try:
        file_domain_list = load_domains_from_file(args.file)
        nameserver_list = load_nameservers_from_file(NAMESERVERS_FILE_PATH)
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    if args.remove:
        remove_entries_from_hosts_file(file_domain_list)
    elif args.load:
        test_domains(file_domain_list, nameserver_list)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
