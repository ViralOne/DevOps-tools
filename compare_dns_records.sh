#!/bin/bash

DNS_SERVERS=('provider-1.dns.com' 'provider-2.dns.com' 'provider-3.dns.com')
DNS_SERVER=${DNS_SERVERS[1]}
FILE="results-$1"
SAVE_TO_FILE=true

dns_query() {
  local domain="$1"
    
  local result_ns=$(dig +short "$domain" @"$DNS_SERVER")
  local result_default=$(dig +short "$domain")
  local filtered_result_default=$(echo $result_default | awk '{print $1}')
  
  if [[ "$result_ns" != "$filtered_result_default" ]]; then
    if [[ "$SAVE_TO_FILE" = true ]]; then
      echo "Domain: $domain:" >> "$FILE"
      echo "From default DNS: $filtered_result_default" >> "$FILE"
      echo -e "From $DNS_SERVER DNS: $result_ns\n" >> "$FILE"
    else
      echo "Domain: $domain:"
      echo "From default DNS: $filtered_result_default"
      echo -e "From $DNS_SERVER DNS: $result_ns\n"
    fi
  fi
}

while IFS= read -r line; do
  dns_query "$line"
done < "$1"

exit 0
