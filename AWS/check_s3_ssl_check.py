# Check S3 Bucket to have: 
# policy.Statement with [Effect='Deny' and Condition.Bool.aws:SecureTransport='false']
# and policy.Statement contain [Action contain ['s3:GetObject'] or Action contain ['s3:*']or Action contain ['*']]

import boto3
import json
import sys, signal
from concurrent.futures import ThreadPoolExecutor

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3_client = session.client('s3')

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

def check_bucket_secure_transport(bucket_name):
    try:
        # Get the bucket policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)

        # Parse the policy JSON
        policy_json = json.loads(bucket_policy['Policy'])

        deny_secure_transport = False
        specific_actions_allowed = False

        # Iterate through policy statements
        for statement in policy_json.get('Statement', []):
            effect = statement.get('Effect', 'Allow')
            conditions = statement.get('Condition', {})
            actions = statement.get('Action', [])

            # Check if the statement denies unsecured transport and allows specific actions
            if (
                effect == 'Deny'
                and conditions.get('Bool', {}).get('aws:SecureTransport') == 'false'
                and (
                    any(action.startswith('s3:GetObject') for action in actions)
                    or any(action == 's3:*' or action == '*' for action in actions)
                )
            ):
                deny_secure_transport = True
            elif (
                effect == 'Allow'
                and (
                    any(action.startswith('s3:GetObject') for action in actions)
                    or any(action == 's3:*' or action == '*' for action in actions)
                )
            ):
                specific_actions_allowed = True

        # Check the conditions and print the result
        if deny_secure_transport and specific_actions_allowed:
            print(f"Bucket {bucket_name} meets the desired conditions.")
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
        executor.submit(check_bucket_secure_transport, bucket_name)
