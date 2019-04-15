import boto3
import json
import datetime
import uuid
import time
from datetime import timezone
from testrail import Testrail


username = "shreyasj@velocloud.net"
password = "Cisco123"
tt = Testrail(user=username, password=password)


def producer(event, context):
    sns = boto3.client('sns')

    context_parts = context.invoked_function_arn.split(':')
    topic_name = "marks-blog-topic"
    topic_arn = "arn:aws:sns:{region}:{account_id}:{topic}".format(
        region=context_parts[3], account_id=context_parts[4], topic=topic_name)

    now = datetime.datetime.now(timezone.utc)
    start_date = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")
    rrr = tt.get_users()
    # params = {"startDate": start_date, "endDate": end_date, "tags": ["neo4j"]}
    params = {"get_users": rrr}

    sns.publish(TopicArn= topic_arn, Message= json.dumps(params))

    body = {
        "message": "BRO...! Your function executed successfully!",
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response


def consumer(event, context):
    for record in event["Records"]:
        message = json.loads(record["Sns"]["Message"])

        get_users = message["get_users"]
        print("start_date: " + str(get_users))

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("notes")
        item = {
            'noteId': str(uuid.uuid1()),
            'userId': "bro",
            'get_users': get_users,
            'createdAt': int(time.time() * 1000)
        }

        # write the todo to the database
        table.put_item(Item=item)
