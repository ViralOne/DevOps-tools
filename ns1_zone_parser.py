import json
import argparse
from datetime import datetime

def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("Error occurred while reading the input file:", str(e))
        exit()

def write_soa_record(file, data):
    file.write(f';; Domain:  {data["name"]}.\n')
    file.write(f';; Exported:  {datetime.fromtimestamp(data["created_at"])}\n\n')
    file.write(f'$ORIGIN {data["name"]}\n')
    file.write(f'$TTL {data["nx_ttl"]}\n')

def write_records(file, record_type, records, record_ttls):
    if len(records) > 0:
        file.write(f'\n;; {record_type} Records\n')
        for domain, content in records.items():
            content = content.rstrip('.')
            answers = [answer for answer in content.split()]

            ttl = record_ttls[record_type][domain]

            if answers:
                file.write(f"{domain}\t{ttl}\tIN\t{record_type}\t{answers[0] if len(answers) == 1 else ' '.join(answers)}.\n")

def main():
    parser = argparse.ArgumentParser(description='Convert NS1 JSON zone file to DNS zone file.')
    parser.add_argument('file', help='Input JSON file name')
    args = parser.parse_args()

    data = load_json(args.file)

    zone_name = data['name']
    records = data['records']

    # Open the zone file
    with open(f'{zone_name}.zone', 'w') as f:
        write_soa_record(f, data)

        record_types = {'CNAME': {}, 'A': {}, 'AAAA': {}, 'TXT': {}, 'MX': {}, 'SOA': {}, 'NS': {}}
        record_ttls = {record_type: {} for record_type in record_types}

        for record in records:
            domain = record['domain']
            type_ = record['type']

            record_types[type_][domain] = record['short_answers'][0].split()[-1] if record.get('short_answers') else ''
            record_ttls[type_][domain] = record['ttl']

        for record_type, records in record_types.items():
            write_records(f, record_type, records, record_ttls)

    record_counts = {record_type: len(records) for record_type, records in record_types.items()}
    
    for record_type, count in record_counts.items():
        if count != 0:
            print(f"Found {count} records of type {record_type}")

if __name__ == "__main__":
    main()
