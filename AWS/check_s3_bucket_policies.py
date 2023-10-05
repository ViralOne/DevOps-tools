# Check if S3 buckets are publicly accessible

import boto3
import sys, signal

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3 = session.client('s3')

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

try:
    response = s3.list_buckets()
    buckets = response['Buckets']
    if buckets:
        print("List of S3 buckets:")
        for bucket in buckets:
            try:
                policy_s3 = s3.get_bucket_policy(Bucket=bucket['Name'])
                # print(policy_s3)
                print(f"Policy exists for {bucket['Name']}")
            except Exception as e:
                    print(f"An error occurred: {e}")
    else:
        print("No S3 buckets found in the account.")
except Exception as e:
    print(f"An error occurred: {e}")
