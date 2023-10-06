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
                    executor.submit(check_bucket_accessibility, s3_client, bucket_name)
        else:
            logger.info("No S3 buckets found in the account.")
    except Exception as e:
        logger.error("An error occurred: %s",e)

def is_bucket_public(s3_client, bucket_name):
    try:
        # Check bucket ACL for public access
        response = s3_client.get_bucket_acl(Bucket=bucket_name)
        for grant in response['Grants']:
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group' and grantee.get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                return True
        # Check bucket policy for public access
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy = response.get('Policy')
        if policy and '"Effect": "Allow", "Principal": "*"' in policy:
            return True
        return False
    except Exception as e:
        logger.error("An error occurred while checking %s: %s", bucket_name, e)
        return False

def check_bucket_accessibility(s3_client, bucket_name):
    if not is_bucket_public(s3_client, bucket_name):
        logger.info("%s is not publicly accessible.", bucket_name)
    else:
        logger.info("%s is publicly accessible.", bucket_name)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
