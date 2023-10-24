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
        
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        if buckets:
            logger.info("List of S3 buckets:")
            with ThreadPoolExecutor(MAX_WORKERS) as executor:
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    executor.submit(check_s3_static_website, s3_client, bucket_name)
        else:
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error("An error occurred: %s", e)

def check_s3_static_website(s3_client, bucket_name):
    try:
        static_website = s3_client.get_bucket_website(Bucket=bucket_name)
        logger.warn("Website hosting is enabled for %s", bucket_name)
    except Exception as e:
        logger.info("An error occurred for bucket %s: %s", bucket_name, e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
