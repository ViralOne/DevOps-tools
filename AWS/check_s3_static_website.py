# Check where Static website hosting is disabled on your S3 bucket

import boto3
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3 = session.client('s3')

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

def check_s3_static_website(bucket_name):
    try:
        static_website = s3.get_bucket_website(Bucket=bucket_name)
        print(f"Website hosting is enabled for {bucket_name}")
    except Exception as e:
        if 'NoSuchWebsiteConfiguration' in str(e):
            print(f"Website hosting is disabled for {bucket_name}")
        else:
            print(f"An error occurred for bucket {bucket_name}: {e}")

def main():
    try:
        response = s3.list_buckets()
        buckets = response['Buckets']
        if buckets:
            print("List of S3 buckets:")
            with ThreadPoolExecutor(max_workers=10) as executor:
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    executor.submit(check_s3_static_website, bucket_name)
        else:
            print("No S3 buckets found in the account.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
