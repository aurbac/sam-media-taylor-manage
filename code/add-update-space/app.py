import json
import os
import datetime
import time
import boto3

def lambda_handler(event, context):

    print(event)
    
    #convertir json string a objeto
    data = json.loads(event["body"])
    
    print("----")
    print(data)
    
    SPACES_TABLE = os.environ['SPACES_TABLE']
    MEDIA_TABLE = os.environ['MEDIA_TABLE']
    
    mediaToSave = []
    for item in data['media']:
        if item["selected"]==True:
            mediaToSave.append(item["media_id"])
            
    
    t=data['dateTime']  
    new_time=datetime.datetime.strptime(t,"%Y-%m-%dT%H:%M:%S.%fZ")
    new_time = new_time.replace(second=0, microsecond=0)
    #new_time_python=datetime.datetime.strftime(new_time,"%m-%d-%y")
    time_stamp = str(time.mktime(new_time.timetuple()))
    
    client = boto3.client("dynamodb")
    
    response = client.update_item(
        TableName=SPACES_TABLE,
        Key= {
            'channel_id': {
                'S': data["channel"]
            },
            "time_stamp": {
                'N': time_stamp
            }
        },
        AttributeUpdates={
            'media': {
                'Value': { 'SS': mediaToSave } , 'Action': 'PUT'
            },
            'date_time': {
                'Value': { 'S': data['dateTime'] }, 'Action': 'PUT'
            }
        }
    )

    print (response)
        
    print(mediaToSave)

    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
            },
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
