"""Looks up a requested URI in DynamoDB and returns a redirect.

Returns:
    str -- result of the run

"""
import os
import sys

# import json
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from redirect_utils import str2bool

"""
This function receives a request from an ELB/ALB, looks up the path in DynamoDB, then returns any
redirects that are returned.  If there are no matches, it will check for a regex match to match
an Int'l site and return the appropriate redirect.  As a last resort, it will redirect to a default
location.

Configure these environment variables in your Lambda environment
1. DYNAMO_DB_ARN - The ARN of the DynamoDB instance holding the redirect data
2. DYNAMO_DB_TABLE - The name of the DynamoDB table
3. DEFAULT_DESTINATION_HOST - The host to redirect to if no matches are found
4. DEFAULT_DESTINATION_PATH - The path to redirect to if no matches are found
5. DEFAULT_HTTP_SCHEME - http or https (defaults to https if not defined)
6. DEFAULT_REDIRECT_CODE - Which redirect code to issue (defaults to 301 if not defined)
7. DEFAULT_REDIRECT_DESC - Description of the redirect code to return
"""

DYNAMO_DB_ARN = os.environ["DYNAMO_DB_ARN"]
DYNAMO_DB_TABLE = os.environ["DYNAMO_DB_TABLE"]
DEFAULT_DESTINATION_HOST = os.environ["DEFAULT_DESTINATION_HOST"]
DEFAULT_DESTINATION_PATH = os.environ["DEFAULT_DESTINATION_PATH"]

if "DEFAULT_HTTP_SCHEME" in os.environ:
    DEFAULT_HTTP_SCHEME = os.environ["DEFAULT_HTTP_SCHEME"]
else:
    DEFAULT_HTTP_SCHEME = "https"

if "DEFAULT_REDIRECT_CODE" in os.environ:
    DEFAULT_REDIRECT_CODE = int(os.environ["DEFAULT_REDIRECT_CODE"])
else:
    DEFAULT_REDIRECT_CODE = 301

if DEFAULT_REDIRECT_CODE == 301:
    DEFAULT_REDIRECT_DESC = "301 MOVED PERMANENTLY"
elif DEFAULT_REDIRECT_CODE == 302:
    DEFAULT_REDIRECT_DESC = "302 FOUND"
else:
    DEFAULT_REDIRECT_DESC = "%s UNKNOWN" % DEFAULT_REDIRECT_CODE

if "DEBUG" in os.environ:
    DEBUG = str2bool(os.environ["DEBUG"])
else:
    DEBUG = False

TIME = datetime.strftime(((datetime.utcnow())), "%Y-%m-%d %H:%M:%S")

try:
    ddb = boto3.client("dynamodb")
except Exception as e:
    print("ERROR: failed to connect to DynamoDB")
    sys.exit(1)


def lookup_redirect(hostIn=None, pathIn=None):
    """Look up a redirect in DynamoDB and updates the counters if found.

    Keyword Arguments:
        hostIn {str} -- Requested host (default: {None})
        pathIn {str} -- Requested path (default: {None})

    Returns:
        {str} or {None} -- Redirect location if found, otherwise None
    """
    if hostIn and pathIn:
        if DEBUG:
            print("===== lookup_redirect() DEBUG BEGIN =====")
            print("hostIn: %s" % hostIn)
            print("pathIn: %s" % pathIn)
        try:
            update_response = ddb.update_item(
                TableName=DYNAMO_DB_TABLE,
                Key={"Site": {"S": hostIn}, "URI": {"S": pathIn}},
                UpdateExpression="set HitCount = HitCount + :i, LastHit = :l",
                ExpressionAttributeValues={
                    ":i": {"N": "1"},
                    ":l": {"S": ("%s" % TIME)},
                },
                ReturnValues="ALL_NEW",
            )
        except ClientError as e:
            if DEBUG:
                print("lookup_redirect ERROR: %s" % e.response["Error"]["Message"])
            return False
        else:
            response = update_response["Attributes"]
            redirectLocation = update_response["Attributes"]["RedirectLocation"]["S"]
            if DEBUG:
                print("'response' from DynamoDB: %s" % response)
                print("'redirectLocation' from DynamoDB: %s" % redirectLocation)
            return redirectLocation


def lambda_handler(event, context):
    """Run job when invoked by Lambda.

    Arguments:
        event {obj} -- event that was invoked
        context {obj} -- context of event that was invoked

    """
    httpResponse = {
        "statusCode": DEFAULT_REDIRECT_CODE,
        "statusDescription": DEFAULT_REDIRECT_DESC,
        "isBase64Encoded": False,
        "headers": {"Content-Type": "text/html"},
        "Location": "%s://%s%s"
        % (DEFAULT_HTTP_SCHEME, DEFAULT_DESTINATION_HOST, DEFAULT_DESTINATION_PATH),
    }
    if DEBUG:
        print("===== lambda_handler() DEBUG BEGIN =====")
        print("Event: %s" % event)
        print("\nContext: %s" % context)
    if "path" in event:
        pathIn = event["path"]
        if len(pathIn) > 1:
            pathIn = pathIn.rstrip("/")
    else:
        pathIn = "/"
    if "headers" in event and "host" in event["headers"]:
        hostIn = event["headers"]["host"]
    else:
        hostIn = None

    try:
        redirect = lookup_redirect(hostIn, pathIn)
    except Exception as e:
        if DEBUG:
            print("===== lambda_handler() DEBUG CONTINUE =====")
            print("ERROR: %s" % e)
        pass
    else:
        if DEBUG:
            print("===== lambda_handler() DEBUG CONTINUE =====")
            if not redirect:
                print("NO 'redirect' var found")
            else:
                print("Redirect Location to return to ALB: %s" % redirect)
        if redirect:
            httpResponse["Location"] = redirect

    if DEBUG:
        print("FINAL: %s" % httpResponse)

    return httpResponse
