import boto3
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

def list_aws_profiles():
    """List available AWS profiles."""
    try:
        # Create a session to load AWS profiles
        session = boto3.Session(profile_name=None)

        # Get a list of available profiles
        available_profiles = session.available_profiles

        if not available_profiles:
            return []
        else:
            for profile in available_profiles:
                print("-",profile)
            return available_profiles
    except Exception as e:
        print(f"Error listing AWS profiles: {str(e)}")
        return []

def select_aws_profile_interactively():
    """Select an AWS profile interactively."""
    available_profiles = list_aws_profiles()
    if available_profiles:
        profile_completer = WordCompleter(available_profiles)
        profile_name = prompt('Select an AWS profile: ', completer=profile_completer)

        if profile_name in available_profiles:
            return profile_name
        else:
            print("Invalid profile selected. Please select a valid profile.")
    else:
        print("No AWS profiles found. Please configure AWS profiles in your credentials file.")
    return None
