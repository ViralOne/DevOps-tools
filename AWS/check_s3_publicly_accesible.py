import boto3

profile_name = input("Enter your AWS Profile Name: ")
session = boto3.Session(profile_name=profile_name)
s3 = session.client('s3')

def is_bucket_public(bucket_name):
    try:
        # Check bucket ACL for public access
        response = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in response['Grants']:
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group' and grantee.get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                return True
        # Check bucket policy for public access
        response = s3.get_bucket_policy(Bucket=bucket_name)
        policy = response.get('Policy')
        if policy and 'Effect" : "Allow","Principal": "*" ' in policy:
            return True
        return False
    except Exception as e:
        print(f"An error occurred while checking {bucket_name}: {e}")
        return False
try:
    response = s3.list_buckets()
    buckets = response['Buckets']
    if buckets:
        print("List of S3 buckets:")
        for bucket in buckets:
            bucket_name = bucket['Name']
            if not is_bucket_public(bucket_name):
                print(f"{bucket_name} is not publicly accessible.")
            else:
                print(f"{bucket_name} is publicly accessible.")
    else:
        print("No S3 buckets found in the account.")
except Exception as e:
    print(f"An error occurred: {e}")