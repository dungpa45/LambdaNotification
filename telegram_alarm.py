import json
import os
import logging
import requests
import boto3
# Initializing a logger and settign it to INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Reading environment variables and generating a Telegram Bot API URL
TOKEN = os.environ['TOKEN']
USER_ID = os.environ['USER_ID']
TELEGRAM_URL = "https://api.telegram.org/bot{}/sendMessage".format(TOKEN)
orga_client = boto3.client('organizations')
# Helper function to prettify the message if it's in JSON
def process_message(input):
    try:
        # Loading JSON into a string
        raw_json = json.loads(input)
        # Outputing as JSON with indents
        output = json.dumps(raw_json, indent=4)
    except:
        output = input
    return output

def emoji(NewStateValue):
    if NewStateValue == "ALARM":
        return u'\U0001F621'
    elif NewStateValue == "OK":
        return u'\U0001F60E'
    else:
        return u'\U0001F610'

# Main Lambda handler
def lambda_handler(event, context):
    logger.info(json.dumps(event))

    # Basic exception handling. If anything goes wrong, logging the exception
    try:
        # Reading the message "Message" field from the SNS message
        snsSubject = event['Records'][0]['Sns']['Subject']
        snsMessage = json.loads(event['Records'][0]['Sns']['Message'])
        snsArn = event["Records"][0]["Sns"]["TopicArn"]
        print(snsMessage)

        if snsSubject[0:5] == "ALARM" or snsSubject[0:2] == "OK" or snsSubject[0:12] == "INSUFFICIENT":
            AlarmName = snsMessage['AlarmName']
            AlarmDescription = snsMessage['AlarmDescription']
            if AlarmDescription is None:
                AlarmDescription = " "
            AccountID = snsMessage["AWSAccountId"]
            Account_Name = orga_client.describe_account(AccountId=AccountID)['Account']['Name']
            NewStateValue = snsMessage['NewStateValue']
            OldStateValue = snsMessage['OldStateValue']
            Region = snsMessage['Region']
            Dimensions = str(snsMessage['Trigger']['Dimensions'])
            NewStateReason = snsMessage['NewStateReason']

            if snsArn == "arn:aws:sns:us-east-1:700808010711:OMMS-Alarm-Virginia":
                emo = emoji(NewStateValue)
                tmp = "[SES] ALARMS\n\n[" + NewStateValue + "]  "+ emo+emo+emo + "\nAlarm Name: " + AlarmName + \
                "\n" + AlarmDescription + \
                "\nAccount ID: " + AccountID + \
                "\nAccount Name: " + Account_Name + \
                "\n\nRegion: " + Region + \
                "\nDimensions: " + Dimensions + \
                "\n\nNew State Reason: \n" + NewStateReason
            else:
                emo = emoji(NewStateValue)
                tmp = "OMMS ALARMS\n\n[" + NewStateValue + "]  "+ emo+emo+emo + "\nAlarm Name: " + AlarmName + \
                "\n" + AlarmDescription + \
                "\n\nAccount ID: " + AccountID + \
                "\n\nRegion: " + Region + \
                "\nDimensions: " + Dimensions + \
                "\n\nNew State Reason: \n" + NewStateReason

            message = process_message(tmp)

        elif snsSubject == "RDS Notification Message":
            eventSource = snsMessage['Event Source']
            eventTime = snsMessage['Event Time']
            sourceId = snsMessage['Source ID']
            eventMessage = snsMessage['Event Message']
            emo = u'\U0001F4F7' #camera
            tmp = "[RDS] NOTIFICATION MESSAGE\n" + emo+emo+emo + \
            "\nEvent Source: " + eventSource + \
            "\nSource ID: " + sourceId + \
            "\nEvent time: " + eventTime + \
            "\nMessage: " + eventMessage

            message = process_message(tmp)

        elif snsSubject[0:12] == "Auto Scaling":
            print(snsSubject)
            Description = snsMessage['Description']
            AutoScalingGroupARN = snsMessage['AutoScalingGroupARN']
            AutoScalingGroupName = snsMessage['AutoScalingGroupName']
            Cause = snsMessage['Cause']
            Event = snsMessage['Event']
            if Description[0:11] == "Terminating":
                emo = u'\U0001F480'
            else:
                emo = u'\U0001F607'
            tmp = "[SCALING] NOTIFICATION\n\n" + Event + "  "+emo+emo+emo +\
            "\nGroup: " + AutoScalingGroupName + \
            "\nDescription: " + Description + \
            "\n\nCause: " + Cause

            message = process_message(tmp)

        else:
            tmp = snsMessage
            # print("message: " + tmp)
            message = process_message(tmp)
            print("not noti on telegram")

        # Payload to be set via POST method to Telegram Bot API
        payload = {
            "text": message.encode("utf8"),
            "chat_id": USER_ID
            # "chat_id": 564101049
        }

        # # Posting the payload to Telegram Bot API
        requests.post(TELEGRAM_URL, payload)

    except Exception as e:
        raise e
