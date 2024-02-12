import json
import boto3
import os


def makeObjectFromItem(record):
    result = {}
    for key, value in record.items():
        if 'S' in value:
            result[key] = str(value['S'])
        elif 'N' in value:
            result[key] = float(value['N'])
        elif 'BOOL' in value:
            result[key] = value["BOOL"]
        elif 'SS' in value:
            result[key] = value['SS']
        elif 'M' in value:
            result[key] = makeObjectFromItem(value['M'])
    return result


def get_spaces_items():
    SPACES_TABLE = os.environ['SPACES_TABLE']
    
    dynamodb = boto3.client("dynamodb")
    '''
    response = dynamodb.scan(
        TableName=SPACES_TABLE
    )
    '''
    response = dynamodb.query(
        TableName=SPACES_TABLE,
        ScanIndexForward=False,
        ExpressionAttributeValues={
            ':channel_id': {
                'S': 'Multimedios4',
            },
        },
        KeyConditionExpression='channel_id = :channel_id',
    )
    
    spaces = []
    
    for item in response['Items']:
        spaces.append(makeObjectFromItem(item))
        
    print(spaces)
    return spaces


def lambda_handler(event, context):
    print(event)
    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
            },
        "body": json.dumps(get_spaces_items()),
    }
