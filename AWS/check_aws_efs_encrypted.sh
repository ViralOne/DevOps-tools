#!/bin/bash

# Get a list of all AWS regions
regions=$(aws ec2 describe-regions --output json | jq -r '.Regions[].RegionName')

for region in $regions; do
  # Get a list EFS in the current region
  efs_list=$(aws efs describe-file-systems --region "$region" --query "FileSystems[*].{FileSystemID:FileSystemId}" --output text)
  if [ -z "$efs_list" ]; then
    echo "No EFS found in region $region."
  else
    echo "Checking EFS encryption in $region:"
    for efs in $efs_list; do
      encrypted=$(aws efs describe-file-systems --region "$region" --file-system-id "$efs" --query 'FileSystems[0].Encrypted' --output text)
      if [ -n "$encrypted" ] && [ "$encrypted" == "True" ]; then
        echo "EFS $efs is encrypted."
      else
        echo "EFS $efs does not have encryption enabled."
      fi
    done
  fi
done
