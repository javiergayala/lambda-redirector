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

- `DYNAMO_DB_ARN` - The ARN of the DynamoDB instance holding the redirect data
- `DYNAMO_DB_TABLE` - The name of the DynamoDB table
- `S3_BUCKET_ARN` - The ARN of the S3 bucket that will be triggering the function
- `DEBUG` (Optional) - Set to "True" if you want debug info printed to CloudWatch
