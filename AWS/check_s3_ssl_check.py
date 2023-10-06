import logging
import boto3
import json
from concurrent.futures import ThreadPoolExecutor
from lib import aws_profile_manager
from lib import handle_exit

# Check S3 Bucket to have:
# policy.Statement with [Effect='Deny' and Condition.Bool.aws:SecureTransport='false']
# and policy.Statement contain [Action contain ['s3:GetObject'] or Action contain ['s3:*'] or Action contain ['*']]

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
                    executor.submit(check_bucket_secure_transport, s3_client, bucket_name)
        else:
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error("An error occurred: %s", e)

def check_bucket_secure_transport(s3_client, bucket_name):
    try:
        # Get the bucket policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_json = json.loads(bucket_policy['Policy'])

        deny_secure_transport = False
        specific_actions_allowed = False

        # Iterate through policy statements
        for statement in policy_json.get('Statement', []):
            effect = statement.get('Effect', 'Allow')
            conditions = statement.get('Condition', {})
            actions = statement.get('Action', [])

            # Check if the statement denies unsecured transport and allows specific actions
            if (
                effect == 'Deny'
                and conditions.get('Bool', {}).get('aws:SecureTransport') == 'false'
                and (
                    any(action.startswith('s3:GetObject') for action in actions)
                    or any(action == 's3:*' or action == '*' for action in actions)
                )
            ):
                deny_secure_transport = True
            elif (
                effect == 'Allow'
                and (
                    any(action.startswith('s3:GetObject') for action in actions)
                    or any(action == 's3:*' or action == '*' for action in actions)
                )
            ):
                specific_actions_allowed = True

        # Check the conditions
        if deny_secure_transport and specific_actions_allowed:
            logger.info("Bucket %s meets the desired conditions.", bucket_name)
        else:
            logger.info("Bucket %s does not meet the desired conditions.", bucket_name)
    except s3_client.exceptions.NoSuchBucket:
        logger.info("Bucket %s does not exist.", bucket_name)
    except Exception as e:
        logger.error("Error checking bucket %s: %s", bucket_name, e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
