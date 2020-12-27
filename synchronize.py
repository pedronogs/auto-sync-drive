from __future__ import print_function
import pickle
import json
import os
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

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
                    'credentials.json', API_URL)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.__service = build('drive', 'v3', credentials=creds)
    

    # List all files inside specified Drive folder
    def list_files(self):
        # Call API
        response = self.__service.files().list(q="'{}' in parents".format(CONFIGS['drive_folder_id'])).execute()

        # Return all file names
        files_dic = {"all": response.get('files', []), "names": []}
        for item in files_dic['all']:
            files_dic['names'].append(item['name'])
        
        return files_dic
    

    # Download file from drive to local folder
    def download_file(self, file_id, filename):
        # Request for download API
        request = self.__service.files().get_media(fileId=file_id)
        
        # File stream
        fh = io.BytesIO()

        # Setup request and file stream
        downloader = MediaIoBaseDownload(fh, request)
        
        # Wait while file is being downloaded
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        # Save download buffer to file
        with open("{}/{}".format(CONFIGS['local_folder_path'], filename), 'wb') as out: 
            out.write(fh.getbuffer())

        print("File downloaded successfully: {}".format(filename))


    # Upload file from local to drive folder
    def upload_file(self, filename):
        # Custom file metadata for upload
        file_metadata = {'name': filename, 'parents': [CONFIGS['drive_folder_id']]}

        # File definitions for upload
        media = MediaFileUpload('{}/{}'.format(CONFIGS['local_folder_path'], filename))

        # Send POST request for upload API
        uploaded_files = self.__service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print('File uploaded successfully: {}'.format(filename))


    # Synchronize drive folder with local folder
    def synchronize(self):
        drive_files = self.list_files()
        local_files = list_local_files()

        # Find all different files between drive and local folders
        different_files = list(set(drive_files['names']) ^ set(local_files))

        # Compare files in both folders and download/upload what is needed
        for diff_file in different_files:
            if diff_file in drive_files['names']:
                # Find ID of file to be downloaded
                for f in drive_files['all']:
                    if f['name'] == diff_file:
                        self.download_file(f['id'], f['name'])
            else:
                # Upload file
                self.upload_file(diff_file)
        

# Return list of all files in specified backup folder
def list_local_files():
    return os.listdir(CONFIGS['local_folder_path'])


def main():
    # Load configs file
    try:
        global CONFIGS
        CONFIGS = json.load(open("configs.json", "r", encoding='utf-8'))
    except:
        print("Please rename example file 'configs-example.json' to 'configs.json' and update all fields.")
        return
    
    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.synchronize()


if __name__ == '__main__':
    main()