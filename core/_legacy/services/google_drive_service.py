import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from core.app_paths import get_base_data_dir
from core.logger import log

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def authenticate_drive():

    base_dir = get_base_data_dir()
    token_path = os.path.join(base_dir, "drive_token.pkl")
    cred_path = "client_secret.json"

    creds = None

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_path):

    service = authenticate_drive()

    file_metadata = {
        'name': os.path.basename(file_path)
    }

    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    log(f"Uploaded to Google Drive: {file_path}")