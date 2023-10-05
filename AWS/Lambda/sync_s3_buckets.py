import boto3
import logging

def lambda_handler(event, context):

    # Source and destination bucket names
    source_bucket = 'mybucket'
    destination_bucket = 'testing-mybucket'

    # AWS S3 client
    s3_client = boto3.client('s3')

    try:
        # List objects in the source bucket
        response = s3_client.list_objects_v2(Bucket=source_bucket)

        # Iterate through each object in the source bucket
        for obj in response['Contents']:
            # Get the object key
            key = obj['Key']

            # Copy object from source to destination bucket
            s3_client.copy_object(
                Bucket=destination_bucket,
                CopySource={'Bucket': source_bucket, 'Key': key},
                Key=key
            )

        return {
            'statusCode': 200,
            'body': 'Data sync between S3 buckets completed!'
        }

    except Exception as e:
        logging.error(f"Error syncing data: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'An error occurred during data sync. Please check logs for more details.'
        }
