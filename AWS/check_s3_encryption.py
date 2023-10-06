import boto3
import concurrent.futures
from lib import aws_profile_manager
from lib import handle_exit
import logging

# Constants
MAX_WORKERS = 10

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(profile_name):
    try:
        # Create a session with the selected AWS profile
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3')

        bucket_names = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
        with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
            executor.map(lambda bucket_name: check_bucket_encryption(s3_client, bucket_name), bucket_names)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

def check_bucket_encryption(s3_client, bucket_name):
    try:
        encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
        logger.info(f"Bucket: {bucket_name} - Encryption: {encryption}")
    except Exception as e:
        logger.error(f"Bucket: {bucket_name} - Encryption: Not enabled")

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info(f"Selected AWS Profile: {selected_profile}")
        main(selected_profile)
