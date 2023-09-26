"""
This module script file contains functionality to download relevant emails from gmail
and save them as html files.
"""

import os.path
import base64
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def download_emails():
    # Build the connection to Gmail API
    service = connect_api()
    try:
        # Fetch messages from the inbox -> ID's of messages
        results = service.users().messages().list(userId='me', labelIds=['Label_5261886783796651195']).execute()
        messages = results.get('messages', [])

        if not messages:
            print('No messages found in the inbox.')
            return

        print('Messages in the inbox:')
        for message in messages:
            # Get message info and the actual data payload based on the id from the message dictionary
            message_info = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            payload = message_info.get('payload', {})
            
            subject = None
            string_with_date = None
            sender = None
            for header in payload['headers']:
                #print(header["name"])
                if header["name"] == 'X-Received':
                    string_with_date = header["value"]
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            
            body = None
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/html':
                        body = part['body']['data']
                    #break
            # elif 'body' in payload:
            #     body = payload['body']['data']

            
            if body:
                print(subject)
                body = base64.urlsafe_b64decode(body).decode('utf-8')

                timestamp = extract_timestamp(string_with_date)
                title = timestamp + " " + subject if timestamp else subject
                # Save email as a plain text file
                save_email_as_text(title, body)

        print('PDFs downloaded successfully.')


    except HttpError as error:
        # TODO(developer) - Handle errors from Gmail API.
        print(f'An error occurred: {error}')


def extract_timestamp(string_with_date):
    timestamp = None

    # Define a regular expression pattern to match the timestamp
    timestamp_pattern = r'\w{3}, \d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [-+]\d{4} \(PDT\)'

    # Use re.search to find the first matching timestamp in the input string
    match = re.search(timestamp_pattern, string_with_date)
    if match:
        timestamp = match.group(0)

    return timestamp


def save_email_as_text(title, body):
    # Remove special characters from the subject to create a valid filename
    title = re.sub(r'[^\w\s]', '', title)
    
    # Create a plain text file and save the email body
    with open(f'./email_data_html/{title}.html', 'w', encoding='utf-8') as file:
        file.write(body)


def empty_inbox():
    """Makes an API call to delete all emails in the inbox folder"""
    try:
        label_id = 'INBOX' 
        service = connect_api()
        
        # List emails in the inbox.
        results = service.users().messages().list(userId="me", labelIds=[label_id]).execute()
        messages = results.get('messages', [])

        # Delete each email.
        for message in messages:
            service.users().messages().delete(userId="me", id=message['id']).execute()
        print("Inbox is emptied.")

    except Exception as e:
        print(f"An error occurred: {e}")


def connect_api():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return 
        print('Labels:')
        for label in labels:
            print(label['name'] + '   ' + label['id'])

        return service

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')

