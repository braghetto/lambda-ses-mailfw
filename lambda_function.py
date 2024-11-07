import boto3
import email
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Setup
region = 'AWS-REGION-NAME'
incoming_email_bucket = 'BUCKET-NAME'
incoming_email_prefix = 'BUCKET-PREFIX'
recipient = ['EMAIL-ADDRESS-TO-FORWARD']

def get_message_from_s3(message_id):

    if incoming_email_prefix:
        object_path = (incoming_email_prefix + "/" + message_id)
    else:
        object_path = message_id

    object_http_path = (f"http://s3.console.aws.amazon.com/s3/object/{incoming_email_bucket}/{object_path}?region={region}")

    client_s3 = boto3.client("s3", region)

    object_s3 = client_s3.get_object(Bucket=incoming_email_bucket,
        Key=object_path)

    file = object_s3['Body'].read()

    file_dict = {
        "file": file,
        "path": object_http_path
    }

    return file_dict

def create_message(file_dict):

    mailobject = email.message_from_string(file_dict['file'].decode('utf-8'))

    subject_original = mailobject['Subject']
    subject = "FW: " + subject_original
    original_sender = mailobject['From']
    original_recipient = mailobject['To']

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = original_recipient
    msg['To'] = ','.join(recipient)
    msg['Reply-To'] = original_sender

    body_text = ""
    body_html = ""

    if mailobject.is_multipart():
        for part in mailobject.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body_text += part.get_payload(decode=True).decode(part.get_content_charset())
            elif content_type == "text/html" and "attachment" not in content_disposition:
                body_html += part.get_payload(decode=True).decode(part.get_content_charset())
            elif "attachment" in content_disposition:
                attachment = MIMEApplication(part.get_payload(decode=True))
                attachment.add_header("Content-Disposition", "attachment", filename=part.get_filename())
                msg.attach(attachment)
    else:
        if mailobject.get_content_type() == "text/html":
            body_html = mailobject.get_payload(decode=True).decode(mailobject.get_content_charset())
        else:
            body_text = mailobject.get_payload(decode=True).decode(mailobject.get_content_charset())

    if body_html:
        msg.attach(MIMEText(body_html, "html"))
    else:
        msg.attach(MIMEText(body_text, "plain"))

    message = {
        "Source": original_recipient,
        "Destinations": recipient,
        "Data": msg.as_string()
    }

    return message

def send_email(message):

    client_ses = boto3.client('ses', region)

    try:
        response = client_ses.send_raw_email(
            Source=message['Source'],
            Destinations=message['Destinations'],
            RawMessage={
                'Data':message['Data']
            }
        )
    except ClientError as e:
        output = e.response['Error']['Message']
    else:
        output = "Email sent! Message ID: " + response['MessageId']

    return output

def lambda_handler(event, context):

    message_id = event['Records'][0]['ses']['mail']['messageId']
    print(f"Received message ID {message_id}")

    file_dict = get_message_from_s3(message_id)

    message = create_message(file_dict)

    result = send_email(message)
    print(result)
