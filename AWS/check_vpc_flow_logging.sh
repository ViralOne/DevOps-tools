#!/bin/bash

# Check that VPC Flow Logging is Enabled in all Applicable Regions
# Where vpcs != isEmpty() should have hasVpcFLowLogging='true'

# AWS regions
regions=(
  us-east-1
  us-east-2
  us-west-1
  us-west-2
  eu-north-1
  eu-central-1
  eu-west-1
  eu-west-2
  eu-west-3
  sa-east-1
  ca-central-1
  ap-northeast-1
  ap-northeast-2
  ap-south-1
  ap-southeast-1
  ap-southeast-2
)

for region in "${regions[@]}"; do
  # Get a list of VPCs in the current region
  vpcs=$(aws ec2 describe-vpcs --region "$region" --query 'Vpcs[].VpcId' --output text)

  if [ -z "$vpcs" ]; then
    echo "No VPCs found in region $region."
  else
    echo "Checking VPC Flow Logging status for VPCs in region $region:"
    for vpc in $vpcs; do
      flow_logging=$(aws ec2 describe-flow-logs --region "$region" --filter Name=resource-id,Values="$vpc" --query 'FlowLogs[0].FlowLogStatus' --output text)
      if [ -n "$flow_logging" ] && [ "$flow_logging" == "ACTIVE" ]; then
        echo "VPC $vpc has VPC Flow Logging enabled."
      else
        echo "VPC $vpc does not have VPC Flow Logging enabled."
      fi
    done
  fi
done
