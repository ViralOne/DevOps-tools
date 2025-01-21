import requests
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Function to upload a file directly to S3 from a URL
def upload_file_to_s3_from_url(file_url, bucket_name, s3_file_name):
    s3 = boto3.client('s3')

    try:
        # Create a session
        with requests.Session() as session:
            # Set headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }

            # Stream the file from the URL
            with session.get(file_url, stream=True, headers=headers, timeout=30) as response:
                response.raise_for_status()  # Check for HTTP errors
                print(f"Response Code: {response.status_code}")
                print(f"Response Headers: {response.headers}")

                # Upload the streamed content to S3
                s3.upload_fileobj(response.raw, bucket_name, s3_file_name)

        print(f"Successfully uploaded {s3_file_name} to {bucket_name}")

    except (NoCredentialsError, PartialCredentialsError):
        print("AWS credentials not found or incomplete.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main function
def main():
    # Ask the user for the file URL, S3 bucket name, and S3 file name
    file_url = input("Enter the URL of the file to upload: ")
    bucket_name = input("Enter your S3 bucket name: ")
    s3_file_name = input("Enter the desired S3 file name (including path if needed): ")

    upload_file_to_s3_from_url(file_url, bucket_name, s3_file_name)

if __name__ == '__main__':
    main()
