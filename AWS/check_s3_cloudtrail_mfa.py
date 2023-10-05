# Check that AWS CloudTrail logging bucket has MFA enabled

import boto3
import json
from concurrent.futures import ThreadPoolExecutor
import sys, signal

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3_client = session.client('s3')

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

def check_bucket_mfa(bucket_name):
    try:
        # Get the bucket versioning configuration
        bucket_versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)

        # Get the bucket policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)

        # Parse the policy JSON
        policy_json = json.loads(bucket_policy['Policy'])

        # Check if MFA is enabled (versioning.mfaDelete should not be false)
        if (
            'Status' in bucket_versioning
            and bucket_versioning['Status'] == 'Enabled'
            and 'MFADelete' in bucket_versioning
            and bucket_versioning['MFADelete'] != 'Disabled'
            and any(
                statement.get('Principal', {}).get('Service') == 'cloudtrail.amazonaws.com'
                for statement in policy_json.get('Statement', [])
            )
        ):
            print(f"Bucket {bucket_name} has MFA enabled and allows CloudTrail access.")
        else:
            print(f"Bucket {bucket_name} does not meet the desired conditions.")
    except s3_client.exceptions.NoSuchBucket:
        print(f"Bucket {bucket_name} does not exist.")
    except Exception as e:
        print(f"Error checking bucket {bucket_name}: {str(e)}")

# List all S3 bucket names
response = s3_client.list_buckets()
buckets = response['Buckets']

# Use ThreadPoolExecutor for concurrent checking
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit each bucket for checking
    for bucket in buckets:
        bucket_name = bucket['Name']
        executor.submit(check_bucket_mfa, bucket_name)
