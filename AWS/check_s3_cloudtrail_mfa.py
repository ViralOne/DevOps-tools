import boto3
import json
from concurrent.futures import ThreadPoolExecutor
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

        response = s3_client.list_buckets()
        buckets = response['Buckets']
        if buckets:
            logger.info("List of S3 buckets:")
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    executor.submit(check_bucket_mfa, s3_client, bucket_name)
        else:
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

def check_bucket_mfa(s3_client, bucket_name):
    """Check that AWS CloudTrail logging bucket has MFA enabled"""
    try:
        # Get the bucket versioning configuration
        bucket_versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_json = json.loads(bucket_policy['Policy'])

        # Check if MFA is enabled
        if (
            'Status' in bucket_versioning
            and bucket_versioning['Status'] == 'Enabled'
            and 'MFADelete' in bucket_versioning
            and bucket_versioning['MFADelete'] != 'Disabled'
            and any(
                statement.get('Principal', {}).get('Service') == 'cloudtrail.amazonaws.com'
                for statement in policy_json.get('Statement', [])
            )
        ):
            logger.info(f"Bucket {bucket_name} has MFA enabled and allows CloudTrail access.")
        else:
            logger.info(f"Bucket {bucket_name} does not meet the desired conditions.")
    except s3_client.exceptions.NoSuchBucket:
        logger.info(f"Bucket {bucket_name} does not exist.")
    except Exception as e:
        logger.error(f"Error checking bucket {bucket_name}: {str(e)}")

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info(f"Selected AWS Profile: {selected_profile}")
        main(selected_profile)
