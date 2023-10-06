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
        # Create a session with the selected AWS profile
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3')

        bucket_names = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
        with ThreadPoolExecutor(MAX_WORKERS) as executor:
            executor.map(lambda bucket_name: check_bucket_encryption(s3_client, bucket_name), bucket_names)
    except Exception as e:
        logger.error("An error occurred: %s", e)

def check_bucket_encryption(s3_client, bucket_name):
    try:
        encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
        logger.info("Bucket: %s - Encryption: %s", bucket_name, encryption)
    except Exception as e:
        logger.error("Bucket: %s - Encryption: Not enabled", bucket_name)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
