from __future__ import print_function
import pickle
import json
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

API_URL = ['https://www.googleapis.com/auth/drive']

class Drive():
    def __init__(self):
        creds = None
        
        # Checks if authentication token exists, then load it
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # Create new authencation token if it does not exist or has expired
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.__service = build('drive', 'v3', credentials=creds)
    
    # List all files inside specified Drive folder
    def list_folder_files(self, folder_id):
        # Call API
        response = self.__service.files().list(q="'{}' in parents".format(folder_id)).execute()

        # Save all files inside a variable
        self.files = response.get('files', [])


def main():
    # Load configs file
    try:
        configs = json.load(open("configs.json", "r"))
    except:
        print("Please rename example file 'configs-example.json' to 'configs.json' and update Google Drive FOLDER ID.")
        return
    
    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.list_folder_files(configs['folder_id'])


if __name__ == '__main__':
    main()