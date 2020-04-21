# lambda-redirector

AWS Lambda function to accept traffic from an ALB, lookup redirects from DynamoDB and return the result.

## DynamoDB Table

The Lambda function expects there to be a DynamoDB Table available for use. The general schema for the records should be:

```json
{
  "Site": {
    "S": "blog.domain.com"
  },
  "URI": {
    "S": "/index2.html"
  },
  "RedirectLocation": {
    "S": "https://www.domain2.com/index2.html"
  },
  "HitCount": {
    "N": "0"
  },
  "LastHit": {
    "S": "0000-00-00 00:00:00"
  }
}
```

## Deploying function to Lambda

The included Makefile can generate a zipfile package with the necessary files included for uploading to Lambda. The resulting file will be available at `dist/lambda_redirector.zip`.

```bash
make dist
```

Once the `lambda_redirector.zip` file has been created, you can upload it via the AWS Console, or any other method (`aws-cli`, `ansible`, etc.)

## Importing Data

The `lambda_redirect_importer.py` file can be used to setup Lambda Function that is triggered whenever a particular S3 location is updated with a new/refreshed file containing redirects in CSV format. **It has been determined that the "sweet spot" in regards to maximum file size is about 3,000 lines.** It can be configured to process a CSV file with the following format:

```csv
# Site,URI,RedirectLocation
blog.domain.com,/index2.html,https://www.domain2.com/index2.html
```

## Setting up `lambda_redirect_importer.py`

### `lambda_redirect_importer.py` Requirements

- A Dynamo DB Table setup for records with the schema mentioned above
  - Configure "Auto Scaling" for the table for both `read` and `write` with a minimum capacity of `5`. The maximum capacity can start out at about `20`, but you may need to increase the capacity of the `write` setting if you have a lot of redirects to import.
- An **Private** S3 Bucket to store the files that will need to be imported (e.g. `rs-production-redirects/data`)
- A Lambda function to host this script, that will be triggered by the above S3 Bucket configured with the following changes to the default values:
  - `Timeout`: Change it to a value of `900` seconds (15 minutes)

### `lambda_redirect_importer.py` Environment Variables

When you setup this lambda function, you need to define the following Environment Variables:

- `DYNAMO_DB_ARN`: The ARN of the DynamoDB instance holding the redirect data
- `DYNAMO_DB_TABLE`: The name of the DynamoDB table
- `S3_BUCKET_ARN`: The ARN of the S3 bucket that will be triggering the function
- `DEBUG` _(Optional)_: Set to "True" if you want debug info printed to CloudWatch

## Setting up `lambda_redirector.py` function (w/ DynamoDB)

### `lambda_redirector.py` Requirements

- A Dynamo DB Table setup for records with the schema mentioned above
- The `lambda_redirect_importer.py` function mentioned above for importing the redirects

### `lambda_redirector.py` Environment Variables

- `DEBUG`: Set to `True` to enable debug statements to be sent to CloudWatch
- `DEFAULT_CACHE_MAX_AGE`: The default maximum amount of time to allow a `301` redirect to be cached
- `DEFAULT_DESTINATION_HOST`: The default host to redirect users to if one isn't defined (e.g. `www.host.com`)
- `DEFAULT_DESTINATION_PATH`: The default path to redirect users to if one isn't defined (e.g. `/blog`)
- `DEFAULT_HTTP_SCHEME`: `http` or `https` _(defaults to_ `https` _if not defined)_
- `DEFAULT_REDIRECT_CODE`: HTTP Status Code to return _(defaults to_ `301` _if not defined)_
- `DEFAULT_REDIRECT_DESC`: Description of the redirect code that is returned _(can omit this if the_ `DEFAULT_REDIRECT_CODE` _is set to_ `301` _or_ `302`_)_
- `DYNAMO_DB_ARN`: ARN to the DynamoDB instance to use for looking up redirects
- `DYNAMO_DB_TABLE`: Name of the DynamoDB table where the redirects are stored (e.g. `redirects`)

## `lambda_redirector.py` function (Path Munger w/o DynamoDB)

### `lambda_redirector.py` Requirements (Path Munger version)

Nothing special is required besides this function.

### `lambda_redirector.py` Environment Variables (Path Munger version)

- `DEBUG`: Set to `True` to enable debug statements to be sent to CloudWatch
- `DEFAULT_CACHE_MAX_AGE`: The default maximum amount of time to allow a `301` redirect to be cached
- `DEFAULT_DESTINATION_HOST`: The default host to redirect users to if one isn't defined (e.g. `www.host.com`)
- `DEFAULT_DESTINATION_PATH`: The default path to redirect users to if one isn't defined (e.g. `/blog`)
- `DEFAULT_HTTP_SCHEME`: `http` or `https` _(defaults to_ `https` _if not defined)_
- `DEFAULT_REDIRECT_CODE`: HTTP Status Code to return _(defaults to_ `301` _if not defined)_
- `DEFAULT_REDIRECT_DESC`: Description of the redirect code that is returned _(can omit this if the_ `DEFAULT_REDIRECT_CODE` _is set to_ `301` _or_ `302`_)_
- `PATH_STRIP`: The path _(in RegEx format)_ to strip from the URI in the request, resulting in a simple redirect

## Testing the Lambda Function

Within the Lambda Console under each Function, you can configure a test event by clicking on "_Select a test event_", then "_Configure test events_". The tests are written in JSON format, and need to mimic the type of payload that would be received by the function from it's trigger (the ALB in the case of `lambda_redirector.py`, or S3 in the case of `lambda_redirect_importer.py`). There are some examples located in the `tests` directory of this repo:

- `blogActualRedirect.json`: Sets the `host` to `blog.rackspace.com` and requests a URI that has a redirect within the DynamoDB table. This is to test that the function is able to retrieve the redirect from DynamoDB and construct the redirect response.
- `blogMultislashStripping.json`: Sets the `host` to `blog.rackspace.com` and requests a URI that contains multiple forward slashes (e.g. `//blog/bloggy///blog`). This is to test that multiple/redundant forward slashes are being stripped from the URI before being processed.
- `wwwEnusMultislashStripping.json`: Similar to `blogMultislashStripping.json`, but sets the `host` to `www.rackspace.com`.
- `wwwEnusStripping.json`: Sets the `host` to `www.rackspace.com` and requests a URI that begins with `/en-us`. This is to test the function after it is configured to strip `/en-us` from requests to see if the resulting redirect correctly strips `/en-us` from the URI.
