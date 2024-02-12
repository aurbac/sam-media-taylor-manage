import json
import boto3
import os
import time
from datetime import datetime

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

#create a function to query dynamodb table bases on key value and sort key value
def query_spaces(channel_id, time_stamp_start, time_stamp_end):
    
    dynamodb = boto3.client("dynamodb")
    
    response = dynamodb.query(
        TableName="sam-media-taylor-manage-SpacesTable-AB4URIV3SII4",
        KeyConditionExpression='channel_id = :channel_id AND time_stamp BETWEEN :time_stamp_start AND :time_stamp_end',
        ExpressionAttributeValues={
            ':channel_id': {'S': channel_id},
            ':time_stamp_start': { 'N': str(time_stamp_start) },
            ':time_stamp_end': { 'N': str(time_stamp_end) }
        }
    )
    result = []
    
    print(response)
    
    for item in response['Items']:
        result.append(makeObjectFromItem(item))
    return result

def lambda_handler(event, context):
    print(event)
    
    CHANNEL_ID = "Multimedios4"
    PLAYBACK_CONFIGURATION_NAME = "Mutimedios4"
    
    CLOUDFRONT_ENDPOINT = os.environ['CLOUDFRONT_ENDPOINT']
    BUCKET_NAME = os.environ['BUCKET_NAME']
    SPACES_TABLE = os.environ['SPACES_TABLE']
    MEDIA_TABLE = os.environ['MEDIA_TABLE']
    
    t_start = int(time.time())
    t_end = int(time.time()+600)
    
    spaces = query_spaces(CHANNEL_ID, t_start, t_end)
    
    print(spaces)
    
    s3_client = boto3.client('s3')
    for space in spaces:
        file = "<VAST version=\"3.0\">\n"
        for index, media in enumerate(space['media']):
            
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(MEDIA_TABLE)
            response = table.get_item(
                Key={ "media_id": media }
                )
            file += f"    <Ad sequence=\"{str(index+1)}\">\n"
            file += f"        <InLine>\n"
            file += f"            <AdSystem>2.0</AdSystem>\n"
            file += f"            <AdTitle>ad-{str(index+1)}</AdTitle>\n"
            file += f"            <Impression/>\n"
            file += f"            <Creatives>\n"
            file += f"                <Creative>\n"
            file += f"                    <Linear>\n"
            file += f"                        <Duration>{response['Item']['duration']}</Duration>\n"
            file += f"                        <MediaFiles>\n"
            file += f"                            <MediaFile delivery=\"progressive\" type=\"video/mp4\" width=\"1280\" height=\"720\">\n"
            file += f"                                <![CDATA[{CLOUDFRONT_ENDPOINT}{media}]]>\n"
            file += f"                            </MediaFile>\n"
            file += f"                        </MediaFiles>\n"
            file += f"                    </Linear>\n"
            file += f"                </Creative>\n"
            file += f"            </Creatives>\n"
            file += f"        </InLine>\n"
            file += f"    </Ad>\n"
            
        file += "</VAST>"
        print(file)
        # upload file to s3
        response = s3_client.put_object(
            Body=file,
            Bucket=BUCKET_NAME,
            Key=space['channel_id']+".xml"
        )
        
        client = boto3.client("dynamodb")
        
        response = client.update_item(
            TableName=SPACES_TABLE,
            Key= {
                'channel_id': {
                    'S': space["channel_id"]
                },
                "time_stamp": {
                    'N': str(int(space['time_stamp']))
                }
            },
            AttributeUpdates={
                'ttl': {
                    'Value': { 'N': str(space['time_stamp']+43200) } , 'Action': 'PUT'
                }
            }
        )
        
        mt_client = boto3.client('mediatailor')
        
        response = mt_client.create_prefetch_schedule(
            Consumption={
                'EndTime': datetime.fromtimestamp(space['time_stamp']+300),
                'StartTime': datetime.fromtimestamp(space['time_stamp']-60)
            },
            Name=space["channel_id"]+"-"+str(int(space["time_stamp"])),
            PlaybackConfigurationName=PLAYBACK_CONFIGURATION_NAME,
            Retrieval={
                'EndTime': datetime.fromtimestamp(space['time_stamp']-60),
                'StartTime': datetime.fromtimestamp(space['time_stamp']-360)
            }
        )
        
        print(response)
        
        ml_client = boto3.client('medialive')
        
        response = ml_client.batch_update_schedule(
            ChannelId="7047459",
            Creates={
                'ScheduleActions': [
                    {
                      "ActionName": space["channel_id"]+"-"+str(int(space["time_stamp"])),
                      "ScheduleActionSettings": {
                        "Scte35SpliceInsertSettings": {
                          "Duration": 8100000,
                          "SpliceEventId": 1
                        }
                      },
                      "ScheduleActionStartSettings": {
                        "FixedModeScheduleActionStartSettings": {
                          "Time": space['date_time']
                        }
                      }
                    }
                ]
            },
        )
    
    return True
