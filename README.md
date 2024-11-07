# Lambda-SES-MailFW
A Lambda function to forward emails received by SES.

## Setup
1. Edit the variables: `region`, `incoming_email_bucket`, `incoming_email_prefix`, and `recipient` in the `lambda_function.py` file.
2. Edit `bucket-name`, `account-id`, and `aws-region` in the `bucket_policy.json` and `lambda_role.json` files.
3. Create an S3 bucket and configure its permissions using the `bucket_policy.json` file.
4. Create an IAM policy and a role using the `lambda_role.json` file.
5. Create a Lambda function using the IAM role for permissions and the code from the `lambda_function.py` file.
6. In SES, create an email receiving rule set with a receipt rule.
7. Configure two actions for this receipt rule: 
   - First, to deliver emails to your S3 bucket with the specified prefix.
   - Second, to invoke your Lambda function.