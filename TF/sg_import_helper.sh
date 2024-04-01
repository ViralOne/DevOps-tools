#!/bin/bash

# Set the security group ID
SECURITY_GROUP_ID="sg-123123"

# Initialize port counters
declare -A port_counters=( [80]=0 [443]=0 )
counter_http=0
counter_https=0

port_counter() {
    local port=$1
    ((port_counters[$port]++))
}

# Get a list of security group rules using AWS CLI
RULES=$(aws ec2 describe-security-group-rules --filters Name=group-id,Values=$SECURITY_GROUP_ID --output json)

if [ -z "$RULES" ]; then
    echo "No rules found for security group $SECURITY_GROUP_ID."
    exit 1
fi

for RULE in $(echo "${RULES}" | jq -r '.SecurityGroupRules[] | @base64'); do
    _jq() {
        echo ${RULE} | base64 --decode | jq -r ${1}
    }

    # Extract rule parameters
    IsEgress=$(_jq '.IsEgress')
    FROM_PORT=$(_jq '.FromPort')
    TO_PORT=$(_jq '.ToPort')
    CIDR=$(_jq '.CidrIpv4')
    DESCRIPTION=$(_jq '.Description')

    if [ "$IsEgress" == "true" ]; then
        TYPE="egress"
    else
        TYPE="ingress"
    fi

    # Construct rule description for importing
    RULE_DESC="${TYPE}_${PROTOCOL}_${FROM_PORT}_${TO_PORT}_${CIDR}"

    # Determine the rule type
    if [ "$FROM_PORT" -eq 80 ]; then
        # Import the rule into Terraform with the appropriate name
        echo "terraform import \"aws_security_group_rule.external_users_eks_http[$counter_http]\" ${SECURITY_GROUP_ID}_${RULE_DESC}"
        port_counter "$FROM_PORT"
        ((counter_http++))
    elif [ "$FROM_PORT" -eq 443 ]; then
        # Import the rule into Terraform with the appropriate name
        echo "terraform import \"aws_security_group_rule.external_users_eks_https[$counter_https]\" ${SECURITY_GROUP_ID}_${RULE_DESC}"
        port_counter "$FROM_PORT"
        ((counter_https++))
    fi
done

echo "Port 80 count: ${port_counters[80]}"
echo "Port 443 count: ${port_counters[443]}"
