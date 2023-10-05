#!/bin/bash

# Check if all four required parameters are provided or no arguments are provided
if [ "$#" -ne 4 ] || [ "$#" -eq 0 ]; then
  echo "Error: Please provide all the parameters."
  echo "Usage: $0 <NAMESPACE> <RELEASE_NAME> <RESOURCE_TYPE_FIND> <RESOURCE_TYPE_REPLACE>"
  echo "Example: $0 kube-system sh.helm.release.v1.some-app.v4 policy/v1beta1 policy/v1"
  exit 1
fi

NAMESPACE="$1"
RELEASE_NAME="$2"
RESOURCE_TYPE_FIND="$3"
RESOURCE_TYPE_REPLACE="$4"

# Get the current release data
PATCH_DATA=$(kubectl get secrets -n "$NAMESPACE" "$RELEASE_NAME" -o json |
  jq .data.release -r |
  base64 -d |
  base64 -d |
  gunzip |
  sed "s|$RESOURCE_TYPE_FIND|$RESOURCE_TYPE_REPLACE|g" |
  gzip -c |
  base64 |
  base64)

# Check if kubectl command encountered an error
if [ $? -ne 0 ]; then
  echo "Error: kubectl command encountered an error."
  exit 1
fi

# Perform the patch operation
kubectl patch secret -n "$NAMESPACE" "$RELEASE_NAME" --type='json' -p="[{\"op\":\"replace\",\"path\":\"/data/release\",\"value\":\"$PATCH_DATA\"}]"

# Check if kubectl patch command encountered an error
if [ $? -ne 0 ]; then
  echo "Error: kubectl patch command encountered an error."
  exit 1
fi

echo "Patch operation completed successfully."
