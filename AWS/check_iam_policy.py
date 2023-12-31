import logging
import boto3
from lib import aws_profile_manager
from lib import handle_exit
from typing import Dict, List
import concurrent.futures

# Constants
MAX_WORKERS = 10

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''Check if Trusted Policy Roles are assumed by external entities'''

def create_iam_client(profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        return session.client('iam')
    except Exception as e:
        logger.error("Failed to create IAM client for profile %s: %s", profile_name, str(e))
        return None

def get_role_names(client) -> List[str]:
    roles = []
    try:
        role_paginator = client.get_paginator('list_roles')
        for response in role_paginator.paginate():
            response_role_names = [r.get('RoleName') for r in response.get('Roles', [])]
            roles.extend(response_role_names)
    except Exception as e:
        logger.error("Failed to retrieve role names: %s", str(e))
    return roles

def get_policies_for_roles(client, role_names: List[str]) -> Dict[str, List[Dict[str, str]]]:
    policy_map = {}

    def fetch_policies(role_name):
        try:
            role_policies = []
            policy_paginator = client.get_paginator('list_attached_role_policies')
            for response in policy_paginator.paginate(RoleName=role_name):
                role_policies.extend(response.get('AttachedPolicies', []))
            return role_name, role_policies
        except Exception as e:
            logger.error("Failed to fetch policies for role %s: %s", role_name, str(e))
            return role_name, []

    with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        results = executor.map(fetch_policies, role_names)

    for role_name, policies in results:
        policy_map[role_name] = policies

    return policy_map

def check_assume_role_statements(client, profile_name, role_name, attached_policies):
    has_assume_role = False
    for policy in attached_policies:
        arn = policy.get('PolicyArn', 'N/A')
        policy_name = policy.get('PolicyName', 'N/A')
        try:
            policy = client.get_policy(PolicyArn=arn)
            policy_version = client.get_policy_version(
                PolicyArn=arn,
                VersionId=policy['Policy']['DefaultVersionId']
            )
        except Exception as e:
            logger.error("Failed to fetch policy details for role %s: %s", role_name, str(e))
            continue

        for statement in policy_version['PolicyVersion']['Document']['Statement']:
            if (
                isinstance(statement, dict) and
                statement.get('Effect') == 'Allow'
                and 'Action' in statement
            ):
                if isinstance(statement['Action'], str):
                    actions = [statement['Action']]
                elif isinstance(statement['Action'], list):
                    actions = statement['Action']

                for action in actions:
                    if action == 'sts:AssumeRole':
                        has_assume_role = True
                        break

    if has_assume_role:
        logger.warning("Role %s is using AssumeRole statement in one or more policies", role_name)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        iam_client = create_iam_client(selected_profile)
        if iam_client:
            role_names = get_role_names(iam_client)
            attached_role_policies = get_policies_for_roles(iam_client, role_names)

            for role_name, policies in attached_role_policies.items():
                check_assume_role_statements(iam_client, selected_profile, role_name, policies)
