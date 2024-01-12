import boto3

def lambda_handler(event, context):
    client = boto3.client('mediapackage')
    response = client.list_channels()
    
    encrypted_endpoints = []
    
    for channel in response['Channels']:
        channel_id = channel['Id']
        
        endpoints = client.list_origin_endpoints(ChannelId=channel_id)
        for endpoint in endpoints['OriginEndpoints']:
            endpoint_id = endpoint['Id']
            encryption_type = client.describe_origin_endpoint(Id=endpoint_id)
            if str(encryption_type).find("SAMPLE_AES"):
                encrypted_endpoints.append(endpoint_id)
    
        if not encrypted_endpoints:
            return False
    
    print({'using_encryption': encrypted_endpoints})
    return {'using_encryption': encrypted_endpoints}
