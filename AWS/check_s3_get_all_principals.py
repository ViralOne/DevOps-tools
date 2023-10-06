# Check if the S3 bucket allows GET actions from all principals

import boto3, sys, signal
import json
from concurrent.futures import ThreadPoolExecutor
from lib import handle_exit

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3_client = session.client('s3')

def check_bucket_policy(bucket_name):
    try:
        # Get the bucket policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)

        # Parse the policy JSON
        policy_json = json.loads(bucket_policy['Policy'])

        # Iterate through policy statements
        for statement in policy_json.get('Statement', []):
            effect = statement.get('Effect')
            principals = statement.get('Principal', {})
            actions = statement.get('Action', [])

            if (
                effect == 'Allow'
                and (
                    principals == ''  # Empty Principal
                    or (isinstance(principals, dict) and 'AWS' in principals)  # Principal.AWS
                )
                and any(action.startswith('s3:Get') for action in actions)
            ):
                print(f"Bucket {bucket_name} violates the policy condition.")
                return

        # If no violation found
        print(f"Bucket {bucket_name} does not violate the policy condition.")
    except s3_client.exceptions.NoSuchBucketPolicy:
        print(f"Bucket {bucket_name} does not have a bucket policy.")
    except Exception as e:
        print(f"Error checking policy for bucket {bucket_name}: {str(e)}")

# List all S3 bucket names
response = s3_client.list_buckets()
buckets = response['Buckets']

# Use ThreadPoolExecutor for concurrent checking
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit each bucket for checking
    for bucket in buckets:
        bucket_name = bucket['Name']
        executor.submit(check_bucket_policy, bucket_name)
