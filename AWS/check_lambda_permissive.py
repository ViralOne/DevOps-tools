import logging
import boto3
import botocore.exceptions
import json
from lib import aws_profile_manager
from lib import handle_exit

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_lambda_policies(profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        lambda_client = session.client('lambda')

        # List Lambda functions
        response = lambda_client.list_functions()
        functions = response.get('Functions', [])

        if functions:
            for function in functions:
                function_name = function['FunctionName']
                role_name = function['Role'].split('/')[-1]

                try:
                    # Describe the execution role policy
                    response = lambda_client.get_policy(FunctionName=function_name)
                    policy = json.loads(response['Policy'])

                    # Check if the policy allows overly permissive actions
                    if check_policy_permissions(policy):
                        logger.info("Lambda function %s with role %s has overly permissive policies.", function_name, role_name)
                    else:
                        logger.info("Lambda function %s with role %s does not have overly permissive policies.", function_name, role_name)
                except botocore.exceptions.ClientError as e:
                    # Check if the error is a "ResourceNotFound" error, and continue if it is
                    if e.response.get('Error', {}).get('Code') == 'ResourceNotFoundException':
                        logger.info("Lambda function %s not found.", function_name)
                        continue
                    else:
                        raise  # Re-raise other exceptions
        else:
            logger.info("No Lambda functions found.")
    except Exception as e:
        logger.error("An error occurred: %s", e)

def check_policy_permissions(policy):
    try:
        statements = policy.get('Statement', [])
        for statement in statements:
            effect = statement.get('Effect', '')
            actions = statement.get('Action', [])
            resources = statement.get('Resource', [])

            # Check if the statement allows overly permissive actions
            if (
                effect == 'Allow'
                and (
                    'InvokeFunction' in actions
                    or any('*' in action for action in actions)
                    or any('*' in resource for resource in resources)
                )
            ):
                return True
        return False
    except Exception as e:
        logger.error("Error checking policy permissions: %s", e)
        return False

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        logger.info("Selected AWS Profile: %s",selected_profile)
        check_lambda_policies(selected_profile)
