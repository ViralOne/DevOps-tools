import logging
import boto3
from concurrent.futures import ThreadPoolExecutor
from lib import aws_profile_manager
from lib import handle_exit

# Constants
MAX_WORKERS = 10
SERVICE_PREFIX = 'sqs:'

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_role_policies(role_name, iam_client):
    # Get the role's policies
    role_policies = iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    
    # Check each policy for service permissions
    for policy in role_policies:
        policy_name = policy['PolicyName']
        policy_document = iam_client.get_policy_version(PolicyArn=policy['PolicyArn'], VersionId='v1')['PolicyVersion']['Document']
        
        # Check if the policy grants service permissions
        if 'Statement' in policy_document:
            for statement in policy_document['Statement']:
                if 'Action' in statement and 'Resource' in statement:
                    actions = statement['Action']
                    resources = statement['Resource']
                    
                    # Check if the policy allows any service actions
                    if isinstance(actions, str) and actions.startswith(SERVICE_PREFIX):
                        print(f"Role: {role_name}, Policy: {policy_name}, Action: {actions}, Resource: {resources}")
                    elif isinstance(actions, list):
                        for action in actions:
                            if action.startswith(SERVICE_PREFIX):
                                print(f"Role: {role_name}, Policy: {policy_name}, Action: {action}, Resource: {resources}")

def main(profile_name):
    # Initialize the AWS IAM client
    session = boto3.Session(profile_name=profile_name)
    iam_client = session.client('iam')

    # List all IAM roles
    response = iam_client.list_roles()

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor(MAX_WORKERS) as executor:
        # Submit each role to the executor
        for role in response['Roles']:
            role_name = role['RoleName']
            executor.submit(check_role_policies, role_name, iam_client)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s",selected_profile)
        main(selected_profile)
