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
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error("An error occurred: %s", e)

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
            logger.info("Bucket %s does not have public access block enabled.", bucket_name)
    except s3_client.exceptions.NoSuchBucket:
        logger.error("Bucket %s does not exist.", bucket_name)
    except Exception as e:
        logger.error("Error checking bucket %s: %s", bucket_name, e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
