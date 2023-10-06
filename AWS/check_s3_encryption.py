import boto3
import concurrent.futures
import signal
import sys

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3_client = session.client('s3')

def handle_exit(signal, frame):
    print("Execution stopped by user.")
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

def check_bucket_encryption(bucket_name):
    try:
        encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
        print(f"Bucket: {bucket_name} - Encryption: {encryption}")
    except Exception as e:
        print(f"Bucket: {bucket_name} - Encryption: Not enabled")

def main():
    try:
        bucket_names = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(check_bucket_encryption, bucket_names)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
