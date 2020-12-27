from __future__ import print_function
import pickle
import json
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

API_URL = ['https://www.googleapis.com/auth/drive']
CONFIGS = None

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
    def list_files(self):
        # Call API
        response = self.__service.files().list(q="'{}' in parents".format(CONFIGS['drive_folder_id'])).execute()

        # Get all files inside response
        aux_files = response.get('files', [])

        # Return all file names
        files = []
        for item in aux_files:
            files.append(item['name'])
        
        return files
    
    # Download file from drive to local folder
    def download_file(self):
        return 'download'

    # Upload file from local to drive folder
    def upload_file(self):
        return 'upload'

    # Synchronize drive folder with local folder
    def synchronize(self):
        drive_files = self.list_files()
        local_files = list_local_files()

        # Find all different files between drive and local folders
        different_files = list(set(drive_files) ^ set(local_files))

        # Compare files in both folders and download/upload what is needed
        for diff_file in different_files:
            if diff_file in drive_files:
                print(self.download_file())
            else:
                print(self.upload_file())
        
# Return list of all files in specified backup folder
def list_local_files():
    return os.listdir(CONFIGS['local_folder_path'])

def main():
    # Load configs file
    try:
        global CONFIGS
        CONFIGS = json.load(open("configs.json", "r", encoding='utf-8'))
    except:
        print("Please rename example file 'configs-example.json' to 'configs.json' and update Google Drive FOLDER ID.")
        return
    
    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.synchronize()


if __name__ == '__main__':
    main()