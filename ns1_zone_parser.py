import json
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description='Convert NS1 JSON zone file to DNS zone file.')
parser.add_argument('file', help='Input JSON file name')
args = parser.parse_args()

with open(args.file, 'r') as f:
    data = json.load(f)

zone_name = data['name']
records = data['records']
exported_date = datetime.fromtimestamp(data["created_at"])

# Open the zone file
with open(f'{zone_name}.conf', 'w') as f:
    # Write the SOA record
    f.write(f'; Zone:  {data["name"]}.\n')
    f.write(f'; Exported :  {exported_date}\n\n')
    f.write(f'$ORIGIN {data["name"]}\n')
    f.write(f'$TTL {data["nx_ttl"]}\n')
    
    # Write the DNS records
    for record in records:
        domain = record['domain']
        type_ = record['type']
        
        if 'CNAME' in type_:
            answers = record['short_answers'][0] if record.get('short_answers') else ''
        # elif 'A' in type_:
        #     answers = record['short_answers'][0].split()[-1] if record.get('short_answers') else ''
        # Add more conditions for other types if needed
        
        f.write(f"{domain} 3600 IN {type_.upper()} {answers}.\n")
