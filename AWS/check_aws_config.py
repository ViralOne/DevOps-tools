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
        client = session.client('config')

        # Get the AWS Config delivery channels
        delivery_channel_response = client.describe_delivery_channels()

        if 'DeliveryChannels' in delivery_channel_response:
            delivery_channel_status = delivery_channel_response['DeliveryChannels'][0]

            logger.info("AWS Config delivery channel is configured.")
            logger.info("S3 Bucket Name: %s", delivery_channel_status.get('s3BucketName', 'Not configured'))
            logger.info("SNS Topic ARN: %s", delivery_channel_status.get('snsTopicARN', 'Not configured'))
        else:
            logger.info("AWS Config delivery channel is not found.")
    except Exception as e:
        logger.error("Error checking AWS Config: %s", e)

if __name__ == "__main__":
    selected_profile = aws_profile_manager.select_aws_profile()

    if selected_profile:
        logger.info("Selected AWS Profile: %s", selected_profile)
        configure_aws_config(selected_profile)
