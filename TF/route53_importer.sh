#! /bin/bash

# All the rights go to Daniel López Azaña
# Link to his blog post: https://www.daniloaz.com/en/how-to-quickly-import-all-records-from-a-route53-dns-zone-into-terraform/
# The script got a few updates to match my needs

# This script retrieves all DNS records from AWS Route53 DNS zone and imports all of them to Terraform

tf_execute=false

# Parse command-line arguments
while getopts ":p:" opt; do
  case ${opt} in
    p )
      aws_profile=$OPTARG
      ;;
    c )
      tf_execute=true
      ;;
    \? )
      echo "Usage: $0 [-p <aws_profile> -c (if argument is pressent it will execute the terraform import)]"
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

# Set AWS profile to default if not provided
aws_profile="${aws_profile:-$default_aws_profile}"

zone_name='example.com'
zone_id='xxxxxxxxxxxxxxxxx'

# Get zone slug from zone name
zone_slug=$(echo ${zone_name} | tr '.' '-')

# Get DNS zone current data from AWS
zone="$(aws --profile=${aws_profile} route53 list-hosted-zones | jq '.HostedZones[] | select (.Id | contains("'${zone_id}'"))')"
# Another method to get DNS zone data searching by zone name instead of zone ID
#zone="$(aws --profile=${aws_profile} route53 list-hosted-zones | jq '.HostedZones[] | select (.Name=="'${zone_name}'.")')"
zone_comment="$(echo ${zone} | jq '.Comment')"
if [ "${zone_comment}" == 'null' ];then
    zone_comment="${zone_name} zone"
fi

# Remove DNS zone file if present
rm dns-zone-${zone_name}.tf

# Write aws_route53_zone resource to terraform file
cat << EOF > dns-zone-${zone_name}.tf
resource "aws_route53_zone" "${zone_slug}" {
    name         = "${zone_name}"
    comment      = "${zone_comment}"
}
EOF

# Import DNS zone and records from file to terraform
if [ "$tf_execute" = true ]; then
    terraform import aws_route53_zone.${zone_slug} ${zone_id}
else
    echo "terraform import aws_route53_zone.${zone_slug} ${zone_id}"
fi

# Retrieve all regular records (not alias) from DNS zone and write them down to terraform file
IFS=$'\n'
for dns_record in $(aws --profile="${aws_profile}" route53 list-resource-record-sets --hosted-zone-id "${zone_id}" | jq -c '.ResourceRecordSets[] | select(has("AliasTarget") | not)');do
    name="$(echo ${dns_record} | jq -r '.Name')"
    type="$(echo ${dns_record} | jq -r '.Type')"
    name_slug="$(echo ${type}-${name} | sed -E 's/[\._\ ]+/-/g' | sed -E 's/(^-|-$)//g')"
    ttl="$(echo ${dns_record} | jq -r '.TTL')"
    records="$(echo ${dns_record} | jq -cr '.ResourceRecords' | jq '.[].Value' | sed 's/$/,/')"
    records="$(echo ${records} | sed 's/,$//')"

    cat << EOF >> dns-zone-${zone_name}.tf

resource "aws_route53_record" "${name_slug}" {
    zone_id = aws_route53_zone.${zone_slug}.zone_id
    name    = "${name}"
    type    = "${type}"
    ttl     = "${ttl}"
    records = [${records}]
}
EOF

    # Import DNS record to Terraform
    if [ "$tf_execute" = true ]; then
        terraform import aws_route53_record.${name_slug} ${zone_id}_${name}_${type}
    else
        echo "terraform import aws_route53_record.${name_slug} ${zone_id}_${name}_${type}"
    fi
done

# Retrieve all alias records from DNS zone and write them down to terraform file
IFS=$'\n'
for dns_record in $(aws --profile="${aws_profile}" route53 list-resource-record-sets --hosted-zone-id "${zone_id}" | jq -c '.ResourceRecordSets[] | select(has("AliasTarget"))');do
    name="$(echo ${dns_record} | jq -r '.Name')"
    type="$(echo ${dns_record} | jq -r '.Type')"
    name_slug="$(echo ${type}-${name} | sed -E 's/[\._\ ]+/-/g' | sed -E 's/(^-|-$)//g')"
    alias_name="$(echo ${dns_record} | jq -cr '.AliasTarget' | jq -r '.DNSName')"

    cat << EOF >> dns-zone-${zone_name}.tf

resource "aws_route53_record" "${name_slug}" {
    zone_id = aws_route53_zone.${zone_slug}.zone_id
    name    = "${name}"
    type    = "${type}"

    alias {
        name                   = "${alias_name}" 
        zone_id                = "${zone_id}"
        evaluate_target_health = true
    }
}
EOF

    # Import DNS record to Terraform
    if [ "$tf_execute" = true ]; then
        terraform import aws_route53_record.${name_slug} ${zone_id}_${name}_${type}
    else
        echo "terraform import aws_route53_record.${name_slug} ${zone_id}_${name}_${type}"
    fi
done

# Fix records if `\"` is found
sed -i 's/\\\"//g' "dns-zone-${zone_name}.tf"
