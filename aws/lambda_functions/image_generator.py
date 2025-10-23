import json
import boto3
import base64
import os
from datetime import datetime
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
s3 = boto3.client('s3', region_name='us-west-2')

# DynamoDB tables
generation_requests_table = dynamodb.Table('echo_generation_requests')
user_sessions_table = dynamodb.Table('echo_user_sessions')

def lambda_handler(event, context):
    """
    AWS Lambda function for scalable image generation
    Handles unlimited client revisions without infrastructure scaling costs
    """
    try:
        # Parse the incoming request
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        user_id = body.get('user_id')
        requirements = body.get('requirements')
        session_id = body.get('session_id', str(uuid.uuid4()))
        
        if not user_id or not requirements:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'user_id and requirements are required'
                })
            }
        
        # Store generation request in DynamoDB
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        generation_requests_table.put_item(
            Item={
                'request_id': request_id,
                'user_id': user_id,
                'session_id': session_id,
                'requirements': requirements,
                'status': 'processing',
                'timestamp': timestamp,
                'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hour TTL
            }
        )
        
        # Generate image using AWS Bedrock
        image_url = generate_image_with_bedrock(requirements, request_id)
        
        # Update request status and store result
        generation_requests_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, image_url = :url, completed_at = :completed',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':url': image_url,
                ':completed': datetime.utcnow().isoformat()
            }
        )
        
        # Update user session with latest generation
        user_sessions_table.put_item(
            Item={
                'user_id': user_id,
                'session_id': session_id,
                'latest_request_id': request_id,
                'latest_image_url': image_url,
                'last_updated': timestamp,
                'total_generations': get_user_generation_count(user_id) + 1
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'request_id': request_id,
                'image_url': image_url,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        
        # Update request status to failed if request_id exists
        if 'request_id' in locals():
            try:
                generation_requests_table.update_item(
                    Key={'request_id': request_id},
                    UpdateExpression='SET #status = :status, error_message = :error',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':error': str(e)
                    }
                )
            except:
                pass
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


def generate_image_with_bedrock(requirements, request_id):
    """Generate image using AWS Bedrock Stable Diffusion"""
    try:
        payload = {
            "prompt": f"Professional design concept: {requirements}",
            "mode": "text-to-image",
            "output_format": "png",
            "seed": 0,
            "aspect_ratio": "1:1"
        }
        
        response = bedrock.invoke_model(
            modelId="stability.stable-image-ultra-v1:1",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        image_base64 = result['images'][0]
        
        # Store image in S3
        bucket_name = os.environ.get('S3_BUCKET', 'echo-generated-images')
        image_key = f"generated/{request_id}.png"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=image_key,
            Body=base64.b64decode(image_base64),
            ContentType='image/png'
        )
        
        # Return S3 URL
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
        return image_url
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise


def get_user_generation_count(user_id):
    """Get total number of generations for a user"""
    try:
        response = generation_requests_table.query(
            IndexName='user_id-timestamp-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            Select='COUNT'
        )
        return response['Count']
    except:
        return 0