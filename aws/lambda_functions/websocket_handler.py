import json
import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
apigateway = boto3.client('apigatewaymanagementapi',
                         endpoint_url=os.environ.get('WEBSOCKET_API_ENDPOINT'))

# DynamoDB tables
connections_table = dynamodb.Table('echo_websocket_connections')
generation_requests_table = dynamodb.Table('echo_generation_requests')

def lambda_handler(event, context):
    """
    AWS Lambda function to handle WebSocket connections for real-time updates
    Supports unlimited client revisions without infrastructure scaling costs
    """
    try:
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        if route_key == '$connect':
            return handle_connect(connection_id, event)
        elif route_key == '$disconnect':
            return handle_disconnect(connection_id)
        elif route_key == 'generation_status':
            return handle_generation_status(connection_id, event)
        elif route_key == 'join_session':
            return handle_join_session(connection_id, event)
        else:
            return {'statusCode': 400, 'body': 'Unknown route'}
            
    except Exception as e:
        logger.error(f"Error in websocket handler: {str(e)}", exc_info=True)
        return {'statusCode': 500, 'body': 'Internal server error'}


def handle_connect(connection_id, event):
    """Handle new WebSocket connection"""
    try:
        # Store connection in DynamoDB
        connections_table.put_item(
            Item={
                'connection_id': connection_id,
                'connected_at': datetime.utcnow().isoformat(),
                'ttl': int(datetime.utcnow().timestamp()) + 3600  # 1 hour TTL
            }
        )
        
        logger.info(f"WebSocket connection established: {connection_id}")
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling connect: {str(e)}")
        return {'statusCode': 500}


def handle_disconnect(connection_id):
    """Handle WebSocket disconnection"""
    try:
        # Remove connection from DynamoDB
        connections_table.delete_item(
            Key={'connection_id': connection_id}
        )
        
        logger.info(f"WebSocket connection closed: {connection_id}")
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {str(e)}")
        return {'statusCode': 200}  # Always return 200 for disconnect


def handle_join_session(connection_id, event):
    """Handle joining a generation session for real-time updates"""
    try:
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('session_id')
        user_id = body.get('user_id')
        
        if not session_id or not user_id:
            send_to_connection(connection_id, {
                'type': 'error',
                'message': 'session_id and user_id required'
            })
            return {'statusCode': 400}
        
        # Update connection with session info
        connections_table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET session_id = :session_id, user_id = :user_id',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':user_id': user_id
            }
        )
        
        # Send confirmation
        send_to_connection(connection_id, {
            'type': 'session_joined',
            'session_id': session_id,
            'message': f'Joined session {session_id} for real-time updates'
        })
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error joining session: {str(e)}")
        return {'statusCode': 500}


def handle_generation_status(connection_id, event):
    """Handle generation status requests"""
    try:
        body = json.loads(event.get('body', '{}'))
        request_id = body.get('request_id')
        
        if not request_id:
            send_to_connection(connection_id, {
                'type': 'error',
                'message': 'request_id required'
            })
            return {'statusCode': 400}
        
        # Get generation status from DynamoDB
        response = generation_requests_table.get_item(
            Key={'request_id': request_id}
        )
        
        if 'Item' not in response:
            send_to_connection(connection_id, {
                'type': 'error',
                'message': 'Generation request not found'
            })
            return {'statusCode': 404}
        
        item = response['Item']
        
        # Send status update
        send_to_connection(connection_id, {
            'type': 'generation_status',
            'request_id': request_id,
            'status': item.get('status'),
            'image_url': item.get('image_url'),
            'error_message': item.get('error_message'),
            'timestamp': item.get('timestamp')
        })
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        return {'statusCode': 500}


def send_to_connection(connection_id, data):
    """Send data to a specific WebSocket connection"""
    try:
        apigateway.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data)
        )
    except apigateway.exceptions.GoneException:
        # Connection is closed, remove from DynamoDB
        try:
            connections_table.delete_item(
                Key={'connection_id': connection_id}
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error sending to connection {connection_id}: {str(e)}")


def broadcast_to_session(session_id, data):
    """Broadcast data to all connections in a session"""
    try:
        # Get all connections for this session
        response = connections_table.scan(
            FilterExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id}
        )
        
        for item in response['Items']:
            connection_id = item['connection_id']
            send_to_connection(connection_id, data)
            
    except Exception as e:
        logger.error(f"Error broadcasting to session {session_id}: {str(e)}")