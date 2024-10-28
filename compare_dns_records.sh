#!/bin/bash

# Usage: ./compare_dns_records.sh [-o output_file] [-p] [-t record_type] <domains_file>
# -o: Specify output file (default: results-<domains_file>)
# -p: Save to file instead of printing to console
# -t: Specify DNS record type (default: A)

DNS_SERVERS=('provider-1.dns.com' 'provider-2.dns.com' 'provider-3.dns.com')
SAVE_TO_FILE=false
RECORD_TYPE="A"
OUTPUT_FILE=""

# Process command line arguments
while getopts ":o:pt:" opt; do
  case $opt in
    o) OUTPUT_FILE="$OPTARG" ;;
    p) SAVE_TO_FILE=true ;;
    t) RECORD_TYPE="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

shift $((OPTIND-1))

# Check if domains file is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [-o output_file] [-p] [-t record_type] <domains_file>"
    exit 1
fi

DOMAINS_FILE="$1"

# Set output file if not specified
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="results-$DOMAINS_FILE"
fi

# Function to query DNS
dns_query() {
    local domain="$1"
    local dns_server="$2"
    if [ -z "$dns_server" ]; then
        dig +short "$RECORD_TYPE" "$domain" 2>/dev/null | head -n1
    else
        dig +short "$RECORD_TYPE" "$domain" @"$dns_server" 2>/dev/null | head -n1
    fi
}

# Function to compare DNS records
compare_dns() {
    local domain="$1"
    local default_result=$(dns_query "$domain" "")
    
    for server in "${DNS_SERVERS[@]}"; do
        local server_result=$(dns_query "$domain" "$server")
        if [ "$server_result" != "$default_result" ]; then
            # Clear the progress line
            printf "\r%*s\r" "$(tput cols)" ""
            
            echo "Domain: $domain"
            echo "Default DNS: ${default_result:-No record found}"
            echo "$server: ${server_result:-No record found}"
            echo ""
            
            if [ "$SAVE_TO_FILE" = true ]; then
                echo "Domain: $domain" >> "$OUTPUT_FILE"
                echo "Default DNS: ${default_result:-No record found}" >> "$OUTPUT_FILE"
                echo "$server: ${server_result:-No record found}" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
            fi
            return
        fi
    done
}

# Main execution
total_domains=$(wc -l < "$DOMAINS_FILE")
current_domain=0

while IFS= read -r domain; do
    ((current_domain++))
    
    # Show progress
    printf "\rProcessing domain %d of %d" "$current_domain" "$total_domains"
    
    compare_dns "$domain"
    
    # Limit parallel processes (removed & from compare_dns call)
    if (( current_domain % 10 == 0 )); then
        wait
    fi
done < "$DOMAINS_FILE"

# Clear the progress line
printf "\r%*s\r" "$(tput cols)" ""

echo "Done processing $total_domains domains."

if [ "$SAVE_TO_FILE" = true ]; then
    echo "Results saved to $OUTPUT_FILE"
fi

exit 0
