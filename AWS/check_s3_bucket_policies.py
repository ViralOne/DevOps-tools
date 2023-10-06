# Check if S3 buckets are publicly accessible

import boto3
from concurrent.futures import ThreadPoolExecutor
from lib import handle_exit

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3 = session.client('s3')

def check_bucket_policy(bucket_name):
    try:
        policy_s3 = s3.get_bucket_policy(Bucket=bucket_name)
        print(f"Policy exists for {bucket_name}")
    except Exception as e:
        print(f"Policy does not exist for {bucket_name}: {e}")

def main():
    try:
        response = s3.list_buckets()
        buckets = response['Buckets']
        if buckets:
            print("List of S3 buckets:")
            with ThreadPoolExecutor(max_workers=10) as executor:
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    executor.submit(check_bucket_policy, bucket_name)
        else:
            print("No S3 buckets found in the account.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
