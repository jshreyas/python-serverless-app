import json

from testrail import Testrail


username = "shreyasj@velocloud.net"
password = "Cisco123"



def hello(event, context):

    tt = Testrail(user=username, password=password)
    # import pdb; pdb.set_trace()
    # tt.get_sections()[-1]
    rrr = tt.get_users()
    # print()

    body = {
        "message": "BRO...Go Serverless v1.0! Your function executed successfully!",
        "input": rrr
    }
    
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
