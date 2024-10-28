#!/bin/bash

SAVE_TO_FILE=false
RECORD_TYPE="A"
OUTPUT_FILE=""
DOMAINS_FILE="$1"
TIMEOUT=2
DNS_SERVERS=()

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] <domains_file>
Options:
    -o OUTPUT_FILE   Specify output file (default: results-<domains_file>)
    -p                Save to file instead of printing to console
    -t RECORD_TYPE    Specify DNS record type (default: A)
    -s DNS_SERVERS    Comma-separated list of DNS servers (required if using -s)
    -T TIMEOUT        Query timeout in seconds (default: 2)
    -h                Show this help message
EOF
    exit 1
}

# Process command line arguments
while getopts ":o:pt:s:T:h" opt; do
  case $opt in
    o) OUTPUT_FILE="$OPTARG" ;;
    p) SAVE_TO_FILE=true ;;
    t) RECORD_TYPE="$OPTARG" ;;
    s) IFS=',' read -ra DNS_SERVERS <<< "$OPTARG" ;;
    T) TIMEOUT="$OPTARG" ;;
    h) show_help ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

shift $((OPTIND-1))

# Check if domains file is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [-o output_file] [-p] [-t record_type] [-s dns_servers] <domains_file>"
    exit 1
fi

DOMAINS_FILE="$1"

# Check if DNS servers are provided if -s is used
if [ "${#DNS_SERVERS[@]}" -eq 0 ]; then
    echo "Error: At least one DNS server must be specified with -s option."
    exit 1
fi

# Set output file if not specified
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="results-$DOMAINS_FILE"
fi

# Function to query DNS
dns_query() {
    local domain="$1"
    local dns_server="$2"
    local result

    if [[ -z "$dns_server" ]]; then
        result=$(dig +short +time="$TIMEOUT" "$RECORD_TYPE" "$domain" 2>/dev/null)
    else
        result=$(dig +short +time="$TIMEOUT" "$RECORD_TYPE" "$domain" @"$dns_server" 2>/dev/null)
    fi

    echo "${result:-NXDOMAIN}"
}

# Function to compare DNS records
compare_dns() {
    local domain="$1"
    local default_result=$(dns_query "$domain" "" | head -n 1)
    
    # Only proceed if the default result is not empty
    if [[ -z "$default_result" || "$default_result" == "NXDOMAIN" ]]; then
        return
    fi

    local results=()
    results+=("$default_result")

    for server in "${DNS_SERVERS[@]}"; do
        local server_result=$(dns_query "$domain" "$server")
        results+=("$server_result")
    done

    # Check if the default result matches any of the other results
    local match_found=false
    for ((i = 1; i < ${#results[@]}; i++)); do
        if [[ "${results[0]}" == "${results[i]}" ]]; then
            match_found=true
            break  # If a match is found, exit the loop
        fi
    done

    # If no matches were found, print the results
    if ! $match_found; then
        # Clear the progress line
        printf "\r%*s\r" "$(tput cols)" ""
        
        echo "Domain: $domain"
        echo "Default DNS: ${default_result}"

        for ((i = 0; i < ${#DNS_SERVERS[@]}; i++)); do
            echo "${DNS_SERVERS[i]}: ${results[i+1]}"
        done
        echo ""

        if [ "$SAVE_TO_FILE" = true ]; then
            echo "Domain: $domain" >> "$OUTPUT_FILE"
            echo "Default DNS: ${default_result}" >> "$OUTPUT_FILE"
            for ((i = 0; i < ${#DNS_SERVERS[@]}; i++)); do
                echo "${DNS_SERVERS[i]}: ${results[i+1]}" >> "$OUTPUT_FILE"
            done
            echo "" >> "$OUTPUT_FILE"
        fi
    fi
}

# Main execution
total_domains=$(wc -l < "$DOMAINS_FILE")
current_domain=0

while IFS= read -r domain; do
    ((current_domain++))
    
    # Show progress
    printf "\rProcessing domain %d of %d" "$current_domain" "$total_domains"
    
    compare_dns "$domain"
done < "$DOMAINS_FILE"

# Clear the progress line
printf "\r%*s\r" "$(tput cols)" ""

echo "Done processing $total_domains domains."

if [ "$SAVE_TO_FILE" = true ]; then
    echo "Results saved to $OUTPUT_FILE"
fi

exit 0
