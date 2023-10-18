#!/bin/bash
# Get a list of all secrets and remove duplicates
secret_list=$(aws secretsmanager list-secrets --output json | jq -r '.SecretList[].Name' | sort | uniq)

for secret in $secret_list; do
  # List encryptions for the secret
  encryption_key=$(aws secretsmanager list-secret-version-ids --secret-id $secret --output json | jq -r '.Versions[].KmsKeyIds[]' |  sort | uniq)
  if [ -z "$encryption_key" ]; then
    echo "$secret - Does not have encryption"
  else
    echo "$secret - is using $encryption_key"
  fi
done
