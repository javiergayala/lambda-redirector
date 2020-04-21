"""Looks up a requested URI in DynamoDB and returns a redirect.

Returns:
    str -- result of the run

"""
import re
import sys

from datetime import datetime

import boto3
from botocore.exceptions import ClientError
import config

from redirect_utils import (
    str2bool,
    sanitize_path,
    strip_path,
    construct_redirect_location,
)

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
        if config.DEBUG:
            print("===== lookup_redirect() config.DEBUG BEGIN =====")
            print("hostIn: %s" % hostIn)
            print("pathIn: %s" % pathIn)
        try:
            update_response = ddb.update_item(
                TableName=config.DYNAMO_DB_TABLE,
                Key={"Site": {"S": hostIn}, "URI": {"S": pathIn}},
                UpdateExpression="ADD HitCount :i SET LastHit = :l",
                ExpressionAttributeValues={
                    ":i": {"N": "1"},
                    ":l": {"S": ("%s" % config.TIME)},
                },
                ReturnValues="ALL_NEW",
            )
        except ClientError as e:
            if config.DEBUG:
                print("lookup_redirect ERROR: %s" % e.response["Error"]["Message"])
            return False
        else:
            response = update_response["Attributes"]
            redirectLocation = update_response["Attributes"]["RedirectLocation"]["S"]
            if config.DEBUG:
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
        "statusCode": config.DEFAULT_REDIRECT_CODE,
        "statusDescription": config.DEFAULT_REDIRECT_DESC,
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "text/html",
            "Location": "%s://%s%s"
            % (
                config.DEFAULT_HTTP_SCHEME,
                config.DEFAULT_DESTINATION_HOST,
                config.DEFAULT_DESTINATION_PATH,
            ),
        },
    }
    if config.DEFAULT_REDIRECT_CODE == 301 and config.DEFAULT_CACHE_MAX_AGE is not None:
        httpResponse["headers"]["Cache-Control"] = (
            "max-age=%s, public" % config.DEFAULT_CACHE_MAX_AGE
        )
    if config.DEBUG:
        print("===== lambda_handler() DEBUG BEGIN =====")
        print("Event: %s" % event)
        print("\nContext: %s" % context)
    if "path" in event:
        pathIn = event["path"]
        if config.DEBUG:
            print("Incoming 'path': %s" % pathIn)
        if len(pathIn) > 1:
            pathIn = sanitize_path(pathIn)
    else:
        pathIn = "/"
    if "headers" in event and "host" in event["headers"]:
        hostIn = event["headers"]["host"]
    else:
        hostIn = None

    if config.PATH_STRIP:
        if config.DEBUG:
            print("Skipping DynamoDB Interaction")
        _path = strip_path(config.PATH_STRIP, pathIn)
        httpResponse["headers"]["Location"] = construct_redirect_location(
            host=config.DEFAULT_DESTINATION_HOST,
            path=_path,
            scheme=config.DEFAULT_HTTP_SCHEME,
        )
    else:
        try:
            redirect = lookup_redirect(hostIn, pathIn)
        except Exception as e:
            if config.DEBUG:
                print("===== lambda_handler() DEBUG CONTINUE =====")
                print("ERROR: %s" % e)
            pass
        else:
            if config.DEBUG:
                print("===== lambda_handler() DEBUG CONTINUE =====")
                if not redirect:
                    print("NO 'redirect' var found")
                else:
                    print("Redirect Location to return to ALB: %s" % redirect)
            if redirect:
                httpResponse["headers"]["Location"] = redirect

    if config.DEBUG:
        print("FINAL: %s" % httpResponse)

    return httpResponse
