import logging
import boto3
from lib import aws_profile_manager
from lib import handle_exit

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info("AWS configuration recorder is set to TRUE")

            # Get the AWS Config delivery channel status
            delivery_channel_response = config_client.describe_delivery_channel_status()
            if 'DeliveryChannelsStatus' in delivery_channel_response:
                delivery_channel_status = delivery_channel_response['DeliveryChannelsStatus'][0]

                if (
                    's3BucketName' in delivery_channel_status
                    or 'snsTopicARN' in delivery_channel_status
                ):
                    logger.info("AWS Config delivery channel is configured.")
                    logger.info("S3 Bucket Name: %s",delivery_channel_status.get('s3BucketName', 'Not configured'))
                    logger.info("SNS Topic ARN: %s",delivery_channel_status.get('snsTopicARN', 'Not configured'))
                else:
                    logger.info("AWS Config delivery channel is not fully configured.")
            else:
                logger.info("AWS Config delivery channel is not found.")
        else:
            logger.info("AWS configuration recorder is set to FALSE")
    except Exception as e:
        logger.error("Error checking AWS Config: %s",e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s",selected_profile)
        configure_aws_config(selected_profile)
