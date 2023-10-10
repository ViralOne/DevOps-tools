import logging
import boto3
from concurrent.futures import ThreadPoolExecutor
from lib import aws_profile_manager
from lib import handle_exit

# Constants
MAX_WORKERS = 10

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3')

        response = s3_client.list_buckets()
        buckets = response['Buckets']
        if buckets:
            bucket_names = [bucket['Name'] for bucket in buckets]
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                executor.map(check_public_access_block, [(s3_client, bucket_name) for bucket_name in bucket_names])
        else:
            print("No S3 buckets found in the account.")
    except Exception as e:
        print(f"An error occurred: {e}")

def check_public_access_block(args):
    s3_client, bucket_name = args
    try:
        response = s3_client.get_public_access_block(Bucket=bucket_name)
        public_access_block = response['PublicAccessBlockConfiguration']
        # If the bucket does not block the public access, print the name of it
        if not (
            public_access_block['BlockPublicAcls']
            and public_access_block['IgnorePublicAcls']
            and public_access_block['BlockPublicPolicy']
            and public_access_block['RestrictPublicBuckets']
        ):
            print(f"Bucket {bucket_name} does not have public access block enabled.")
    except s3_client.exceptions.NoSuchBucket:
        print(f"Bucket {bucket_name} does not exist.")
    except Exception as e:
        print(f"Error checking bucket {bucket_name}: {e}")

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
