import logging
import boto3
from lib import aws_profile_manager
from lib import handle_exit

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(profile_name):
    try:
        # Create a session with the selected AWS profile
        session = boto3.Session(profile_name=profile_name)
        client = session.client('iam')

        response = client.list_users()
        users = response['Users']
        for user in users:
            username = user['UserName']
            accesskeyid = ''
            access_keys = client.list_access_keys(UserName=username)
            for entry in access_keys['AccessKeyMetadata']:
                print(f"{username} - {entry['AccessKeyId']}")
            
    except Exception as e:
        logger.error("An error occurred: %s", e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        main(selected_profile)
