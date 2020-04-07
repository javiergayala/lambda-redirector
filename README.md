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

## Importing Data

The `lambda_redirect_importer.py` file can be used for a Lambda Function that is triggered whenever a particular S3 location is updated with a new/refreshed file. It can be configured to process a CSV file with the following format:

```csv
# Site,URI,RedirectLocation
blog.domain.com,/index2.html,https://www.domain2.com/index2.html
```

### Setting up `lambda_redirect_importer.py`

#### Requirements

- A Dynamo DB Table setup with for records with the schema mentioned above
- An S3 Bucket to store the files that will need to be imported
- A Lambda function to host this script, that will be triggered by the above S3 Bucket

#### Environment Variables

When you setup this lambda function, you need to define the following Environment Variables:

##### `lambda_redirect_importer.py` function

- `DYNAMO_DB_ARN`: The ARN of the DynamoDB instance holding the redirect data
- `DYNAMO_DB_TABLE`: The name of the DynamoDB table
- `S3_BUCKET_ARN`: The ARN of the S3 bucket that will be triggering the function
- `DEBUG` _(Optional)_: Set to "True" if you want debug info printed to CloudWatch

##### `lambda_redirector.py` function (w/ DynamoDB)

- `DEBUG`: Set to `True` to enable debug statements to be sent to CloudWatch
- `DEFAULT_DESTINATION_HOST`: The default host to redirect users to if one isn't defined (e.g. `www.host.com`)
- `DEFAULT_DESTINATION_PATH`: The default path to redirect users to if one isn't defined (e.g. `/blog`)
- `DEFAULT_HTTP_SCHEME`: `http` or `https` _(defaults to_ `https` _if not defined)_
- `DEFAULT_REDIRECT_CODE`: HTTP Status Code to return _(defaults to_ `301` _if not defined)_
- `DEFAULT_REDIRECT_DESC`: Description of the redirect code that is returned _(can omit this if the_ `DEFAULT_REDIRECT_CODE` _is set to_ `301` _or_ `302`_)_
- `DYNAMO_DB_ARN`: ARN to the DynamoDB instance to use for looking up redirects
- `DYNAMO_DB_TABLE`: Name of the DynamoDB table where the redirects are stored (e.g. `redirects`)

##### `lambda_redirector.py` function (Path Munger w/o DynamoDB)

- `DEBUG`: Set to `True` to enable debug statements to be sent to CloudWatch
- `DEFAULT_DESTINATION_HOST`: The default host to redirect users to if one isn't defined (e.g. `www.host.com`)
- `DEFAULT_DESTINATION_PATH`: The default path to redirect users to if one isn't defined (e.g. `/blog`)
- `DEFAULT_HTTP_SCHEME`: `http` or `https` _(defaults to_ `https` _if not defined)_
- `DEFAULT_REDIRECT_CODE`: HTTP Status Code to return _(defaults to_ `301` _if not defined)_
- `DEFAULT_REDIRECT_DESC`: Description of the redirect code that is returned _(can omit this if the_ `DEFAULT_REDIRECT_CODE` _is set to_ `301` _or_ `302`_)_
- `PATH_STRIP`: The path _(in RegEx format)_ to strip from the URI in the request, resulting in a simple redirect
