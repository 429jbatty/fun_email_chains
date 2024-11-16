import base64
import os
import json
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Replace with your actual form ID
FORM_ID = "1xuOX73x4e9QzD_gSoPYUKln3eWdXoVsP2xFQbHJBsts"

# Define the scope (read-only access to form responses)
SCOPES = [
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
]


def get_authenticated_service():
    """
    Establishes an authenticated connection to the Google Forms API.
    """
    creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
                redirect_uri=f"http://localhost:{57738}/",  # Replace with your desired port
            )
            creds = flow.run_local_server(port=57738)

    # Build the service object
    return build("forms", "v1", credentials=creds)


if __name__ == "__main__":
    service = get_authenticated_service()

    # Fetch and print form details
    result = service.forms().get(formId=FORM_ID).execute()
    print(result)
