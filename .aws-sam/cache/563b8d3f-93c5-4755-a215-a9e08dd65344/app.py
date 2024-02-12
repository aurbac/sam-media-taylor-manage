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





def get_media_items_to_add():
    MEDIA_TABLE = os.environ['MEDIA_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(MEDIA_TABLE)
    response = table.scan()
    
    for item in response['Items']:
        item['selected'] = False
    
    return response['Items']


def lambda_handler(event, context):
    print(event)
    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
            },
        "body": json.dumps(get_media_items_to_add())
    }
