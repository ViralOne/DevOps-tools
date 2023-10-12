#!/bin/bash

# Get a list of all AWS regions
regions=$(aws ec2 describe-regions --output json | jq -r '.Regions[].RegionName')

# Loop through each region
for region in $regions
do
  status=$(aws configservice describe-configuration-recorder-status --region $region --output json | jq -r '.ConfigurationRecordersStatus[0].recording')
  if [ "$status" == "true" ]; then
    echo "Recording is enabled in $region"
  else
    echo "Recording is not enabled in $region"
  fi
done
