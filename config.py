"""Configuration file for the lambda_redirector.py module.

This module receives a request from an ELB/ALB, looks up the path in DynamoDB, then returns any
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
8. PATH_STRIP - Path to strip from the request, resulting in a simple redirect (no DynamoDB)
                The path should be in RegEx format (e.g. `/en-us/?`)
"""
import os
from datetime import datetime
from redirect_utils import str2bool

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
    DEFAULT_REDIRECT_DESC = "301 Moved Permanently"
elif DEFAULT_REDIRECT_CODE == 302:
    DEFAULT_REDIRECT_DESC = "302 Found"
else:
    DEFAULT_REDIRECT_DESC = "%s Unknown" % DEFAULT_REDIRECT_CODE

if "PATH_STRIP" in os.environ:
    PATH_STRIP = os.environ["PATH_STRIP"]
else:
    PATH_STRIP = False

if "DEBUG" in os.environ:
    DEBUG = str2bool(os.environ["DEBUG"])
else:
    DEBUG = False

TIME = datetime.strftime(((datetime.utcnow())), "%Y-%m-%d %H:%M:%S")
