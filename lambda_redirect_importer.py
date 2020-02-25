"""Imports new redirects from a CSV file into DynamoDB."""
import os
import sys

# import json

import boto3
from botocore.exceptions import ClientError
from redirect_utils import str2bool

"""
This function receives a trigger from S3 that a new CSV file is available in the S3
bucker.  It then retrieves the CSV file and imports the records into the DynamoDB
redirects table.

Configure these environment variables in your Lambda environment:
1. DYNAMO_DB_ARN - The ARN of the DynamoDB instance holding the redirect data
2. DYNAMO_DB_TABLE - The name of the DynamoDB table
3. S3_BUCKET_ARN - The ARN of the S3 bucket that will be triggering the function
4. DEBUG (Optional) - Set to "True" if you want debug info printed to CloudWatch

"""

DYNAMO_DB_ARN = os.environ["DYNAMO_DB_ARN"]
DYNAMO_DB_TABLE = os.environ["DYNAMO_DB_TABLE"]
S3_BUCKET_ARN = os.environ["S3_BUCKET_ARN"]

if "DEBUG" in os.environ:
    DEBUG = str2bool(os.environ["DEBUG"])
else:
    DEBUG = False

try:
    ddb = boto3.client("dynamodb")
except Exception as e:
    print("ERROR: failed to connect to DynamoDB")
    sys.exit(1)

try:
    s3 = boto3.client("s3")
except Exception as e:
    print("ERROR: failed to connect to S3")
    sys.exit(1)


def importFile(record=None):
    """Import file into DynamoDB.

    Keyword Arguments:
        record {obj} -- Record of the S3 file to import (default: {None})

    Returns:
        [type] -- [description]
    """
    if DEBUG:
        print(record)
    s3Bucket = record["bucket"]
    s3ObjectKey = record["object"]["key"]
    if DEBUG:
        print("--- BEGIN importFile() ---")
        print("S3 Bucket: %s" % s3Bucket)
        print("S3 ObjectKey: %s" % s3ObjectKey)
    if s3Bucket["arn"] != S3_BUCKET_ARN:
        print("SKIPPING %s! WRONG S3 BUCKET!!!" % s3ObjectKey)
        return False
    try:
        s3File = s3.get_object(Bucket=s3Bucket["name"], Key=s3ObjectKey)
    except Exception as e:
        print("ERROR IMPORTING %s: %s" % (s3ObjectKey, e))
        return False

    print(s3File["Body"].read())

    return True


def lambda_handler(event, context):
    """Run job when invoked by Lambda.

    Arguments:
        event {obj} -- event that was invoked
        context {obj} -- context of event that was invoked

    """
    s3Records = event["Records"]
    for record in s3Records:
        importFile(record["s3"])
