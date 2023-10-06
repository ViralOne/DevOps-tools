from lib import aws_profile_manager
import boto3

def configure_aws_config(profile_name):
    """Configure AWS Config and check its status."""
    try:
        # Create a session with the selected AWS profile
        session = boto3.Session(profile_name=profile_name)
        config_client = session.client('config')

        # Get the AWS Config configuration recorder status
        response = config_client.describe_configuration_recorder_status()
        config_recorder_status = response['ConfigurationRecordersStatus'][0]

        # Check if recording is on
        if config_recorder_status['recording'] == 'true':
            print("AWS configuration recorder is set to TRUE")

            # Get the AWS Config delivery channel status
            delivery_channel_response = config_client.describe_delivery_channel_status()
            if 'DeliveryChannelsStatus' in delivery_channel_response:
                delivery_channel_status = delivery_channel_response['DeliveryChannelsStatus'][0]

                if 's3BucketName' in delivery_channel_status or 'snsTopicARN' in delivery_channel_status:
                    print("AWS Config delivery channel is configured.")
                    print(f"S3 Bucket Name: {delivery_channel_status.get('s3BucketName', 'Not configured')}")
                    print(f"SNS Topic ARN: {delivery_channel_status.get('snsTopicARN', 'Not configured')}")
                else:
                    print("AWS Config delivery channel is not fully configured.")
            else:
                print("AWS Config delivery channel is not found.")
        else:
            print("AWS configuration recorder is set to FALSE")
    except Exception as e:
        print(f"Error checking AWS Config: {str(e)}")

if __name__ == "__main__":
    # Select an AWS profile interactively
    selected_profile = aws_profile_manager.select_aws_profile_interactively()

    if selected_profile:
        print(f"Selected AWS Profile: {selected_profile}")
        configure_aws_config(selected_profile)
