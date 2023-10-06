import logging
import boto3
import json
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
                # Submit each bucket for checking
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    executor.submit(check_bucket_policy, s3_client, bucket_name)
        else:
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error("An error occurred: %s", e)

def check_bucket_policy(s3_client, bucket_name):
    """Check if the S3 bucket allows GET actions from all principals"""
    try:
        # Get the bucket policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_json = json.loads(bucket_policy['Policy'])

        # Iterate through policy statements
        for statement in policy_json.get('Statement', []):
            effect = statement.get('Effect')
            principals = statement.get('Principal', {})
            actions = statement.get('Action', [])

            if (
                effect == 'Allow'
                and (
                    principals == ''  # Empty Principal
                    or (isinstance(principals, dict) and 'AWS' in principals)  # Principal.AWS
                )
                and any(action.startswith('s3:Get') for action in actions)
            ):
                logger.info("Bucket %s violates the policy condition.", bucket_name)
                return

        # If no violation found
        logger.info("Bucket %s does not violate the policy condition.", bucket_name)
    except s3_client.exceptions.NoSuchBucketPolicy:
        logger.info("Bucket %s does not have a bucket policy.", bucket_name)
    except Exception as e:
        logger.error("Error checking policy for bucket %s: %s", bucket_name, e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
