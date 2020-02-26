"""Imports new redirects from a CSV file into DynamoDB."""
import csv
import os
import sys

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
FIELDNAMES = ("site", "from_uri", "redirect_to")

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


def readCsv(csvData=None):
    """Read CSV Data."""
    print("===== BEGIN readCsv() =====")
    if not csvData:
        print("ERROR: NO CSV DATA")
        return False
    csvReader = csv.DictReader(csvData, fieldnames=FIELDNAMES)
    injectResults = []
    for row in csvReader:
        injectResults.append(injectRecord(row))
    print("===== END readCsv() =====")
    return injectResults


def injectRecord(row=[]):
    """Inject a record into DynamoDB."""
    if DEBUG:
        print("===== injectRecord() DEBUG BEGIN =====")
        print("site: %s" % row["site"])
        print("from_uri: %s" % row["from_uri"])
        print("redirect_to: %s" % row["redirect_to"])
    from_uri_sanitized = row["from_uri"].rstrip("/")
    try:
        update_response = ddb.update_item(
            TableName=DYNAMO_DB_TABLE,
            Key={
                "Site": {"S": ("%s" % row["site"])},
                "URI": {"S": ("%s" % from_uri_sanitized)},
            },
            UpdateExpression="SET RedirectLocation = :l",
            ExpressionAttributeValues={":l": {"S": ("%s" % row["redirect_to"])},},
        )
    except ClientError as e:
        if DEBUG:
            print("injectRecord ERROR: %s" % e.response["Error"]["Message"])
        return False
    else:
        if DEBUG:
            print("'response' from DynamoDB: %s" % update_response)
        return update_response


def importFile(record=None):
    """Import file into DynamoDB.

    Keyword Arguments:
        record {obj} -- Record of the S3 file to import (default: {None})

    Returns:
        [type] -- [description]
    """
    s3Bucket = record["bucket"]
    s3ObjectKey = record["object"]["key"]
    importResult = None
    if DEBUG:
        print("===== BEGIN importFile() =====")
        print("S3 Bucket: %s" % s3Bucket)
        print("S3 ObjectKey: %s" % s3ObjectKey)
    if s3Bucket["arn"] != S3_BUCKET_ARN:
        print("SKIPPING %s! WRONG S3 BUCKET!!!" % s3ObjectKey)
        print("===== ABORT importFile() =====")
        return False
    try:
        s3File = s3.get_object(Bucket=s3Bucket["name"], Key=s3ObjectKey)
    except Exception as e:
        print("ERROR IMPORTING %s: %s" % (s3ObjectKey, e))
        print("===== ABORT importFile() =====")
        return False

    # csvRaw = s3File["Body"].read().decode()
    importResult = readCsv(s3File["Body"].read().decode("utf-8").split("\n"))
    if DEBUG:
        print("===== END importFile() =====")

    return importResult


def lambda_handler(event, context):
    """Run job when invoked by Lambda.

    Arguments:
        event {obj} -- event that was invoked
        context {obj} -- context of event that was invoked

    """
    if DEBUG:
        print("===== BEGIN lambda_handler() =====")
        print("event['Records']: %s" % event["Records"])
    finalResult = []
    filesProcessed = []
    s3Records = event["Records"]
    for record in s3Records:
        filesProcessed.append(
            "%s/%s" % (record["s3"]["bucket"]["arn"], record["s3"]["object"]["key"])
        )
        finalResult = finalResult + importFile(record["s3"])
    if DEBUG:
        print("FINAL RESULT: %s" % finalResult)
        print("NUM OF IMPORTED RECORDS: %s" % len(finalResult))
        print("===== END lambda_handler() =====")
    finalMsg = {
        "NumRecordsImported": len(finalResult),
        "FilesProcessed": filesProcessed,
    }
    return finalMsg
